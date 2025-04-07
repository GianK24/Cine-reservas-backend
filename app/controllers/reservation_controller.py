from flask import Blueprint, request, jsonify, current_app 
from app.models.reservation import Reservation
from app.models.function import Function
from app.services.email_service import send_email

reservation_bp = Blueprint('reservations', __name__)

# Helper: Actualiza el estado de los asientos en la tabla "Asientos"
def update_seat_state(seat_id: str, is_taken: bool):
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table_seats = dynamo_resource.Table('Asientos')
    table_seats.update_item(
        Key={'seat_id': seat_id},
        UpdateExpression="SET is_taken = :val",
        ExpressionAttributeValues={':val': is_taken}
    )

# Endpoint para listar todas las reservas
@reservation_bp.route('/', methods=['GET'])
def get_reservations():
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table = dynamo_resource.Table('Reservas')
    response = table.scan()
    reservations = [Reservation.from_item(item).to_item() for item in response.get('Items', [])]
    return jsonify(reservations), 200

# Endpoint para registrar una nueva reserva
@reservation_bp.route('/', methods=['POST'])
def add_reservation():
    data = request.get_json()
    reservation = Reservation(
    function_id=data.get('function_id'),
    seats_selected=data.get('seats_selected'),
    numeber_seats_selected=data.get('numeber_seats_selected'),
    user_email=data.get('user_email')
    )

    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table_reservations = dynamo_resource.Table('Reservas')
    table_functions = dynamo_resource.Table('Funciones')
    table_movies = dynamo_resource.Table('Peliculas')
    table_rooms = dynamo_resource.Table('Salas')

    # Validar existencia de la función
    function_response = table_functions.get_item(Key={'funcion_id': reservation.function_id})
    if 'Item' not in function_response:
        return jsonify({'error': 'Función no encontrada'}), 404

    funcion_item = function_response['Item']
    function = Function.from_item(funcion_item)

    # Verificar disponibilidad en función según numeber_seats_selected
    if function.available_seats < reservation.numeber_seats_selected:
        return jsonify({'error': 'No hay suficientes asientos disponibles'}), 400

    # Actualizar available_seats en la función
    new_available_seats = function.available_seats - reservation.numeber_seats_selected
    try:
        table_functions.update_item(
            Key={'funcion_id': reservation.function_id},
            UpdateExpression="SET available_seats = :new",
            ExpressionAttributeValues={':new': new_available_seats}
        )
    except Exception as e:
        return jsonify({'error': 'Error al actualizar asientos en la función: ' + str(e)}), 500

    # Marcar cada asiento reservado como ocupado (is_taken = True)
    seat_ids = [s.strip() for s in reservation.seats_selected.split(',') if s.strip()]
    try:
        for seat_id in seat_ids:
            update_seat_state(seat_id, True)
    except Exception as e:
        return jsonify({'error': 'Error al actualizar estado de asientos: ' + str(e)}), 500

    # Guardar la reserva
    try:
        table_reservations.put_item(Item=reservation.to_item())
    except Exception as e:
        return jsonify({'error': 'Error al guardar reserva: ' + str(e)}), 500

    # Enviar notificación de correo usando AWS SES
    ses_client = current_app.config['SES_CLIENT']
    function_response = table_functions.get_item(Key={'funcion_id': reservation.function_id})
    if 'Item' in function_response:
        function = Function.from_item(function_response['Item'])
        # Obtener detalles de película y sala
        movie_response = table_movies.get_item(Key={'pelicula_id': function.movie_id})
        movie_title = movie_response['Item'].get('title') if 'Item' in movie_response else 'Unknown'
        room_response = table_rooms.get_item(Key={'sala_id': function.room_id})
        room_name = room_response['Item'].get('name') if 'Item' in room_response else 'Unknown'
        schedule = function.schedule
    else:
        movie_title = room_name = schedule = 'Unknown'

    subject = "Reserva Confirmada"
    body = (
        f"Su reserva para la película '{movie_title}', en la sala '{room_name}' programada para {schedule} "
        f"ha sido confirmada. (ID: {reservation.reserva_id})"
    )
    send_email(ses_client, reservation.user_email, subject, body)

    return jsonify(reservation.to_item()), 201

# Endpoint para actualizar una reserva existente
@reservation_bp.route('/<string:reserva_id>', methods=['PUT'])
def update_reservation(reserva_id):
    data = request.get_json()
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table_reservations = dynamo_resource.Table('Reservas')
    table_functions = dynamo_resource.Table('Funciones')
    table_movies = dynamo_resource.Table('Peliculas')
    table_rooms = dynamo_resource.Table('Salas')

    existing_response = table_reservations.get_item(Key={'reserva_id': reserva_id})
    if 'Item' not in existing_response:
        return jsonify({'error': 'Reserva no encontrada'}), 404
    existing_reservation = Reservation.from_item(existing_response['Item'])
    old_seats_str = existing_reservation.seats_selected
    old_seats_list = [s.strip() for s in old_seats_str.split(',') if s.strip()]

    # Usar nuevos valores o los existentes
    new_function_id = data.get('function_id', existing_reservation.function_id)
    new_seats_str = data.get('seats_selected', old_seats_str)
    new_seats_list = [s.strip() for s in new_seats_str.split(',') if s.strip()]
    new_user_email = data.get('user_email', existing_reservation.user_email)
    new_number = data.get('numeber_seats_selected', existing_reservation.numeber_seats_selected)

    # Si no hay cambios, no se actualiza
    if (
        new_function_id == existing_reservation.function_id and
        new_seats_str == old_seats_str and
        new_user_email == existing_reservation.user_email
    ):
        return jsonify({'message': 'No se proporcionaron cambios para actualizar'}), 400

    # Calcular diferencia de asientos: Si se liberaron asientos (old - new) o se requieren más (new - old)
    # Convertimos a números:
    seat_diff = existing_reservation.numeber_seats_selected - new_number

    function_response = table_functions.get_item(Key={'funcion_id': new_function_id})
    if 'Item' not in function_response:
        return jsonify({'error': 'Función no encontrada'}), 404
    function = Function.from_item(function_response['Item'])

    # Si se requieren más asientos (seat_diff negativo), verificar disponibilidad
    if seat_diff < 0 and function.available_seats < abs(seat_diff):
        return jsonify({'error': 'No hay suficientes asientos disponibles para la actualización'}), 400

    # Actualizar available_seats en la función
    new_available_seats = function.available_seats + seat_diff
    try:
        table_functions.update_item(
            Key={'funcion_id': new_function_id},
            UpdateExpression="SET available_seats = :new",
            ExpressionAttributeValues={':new': new_available_seats}
        )
    except Exception as e:
        return jsonify({'error': 'Error al actualizar función: ' + str(e)}), 500

    # Actualizar estado de asientos:
    # - Liberar asientos que ya no están en la nueva selección
    seats_to_free = set(old_seats_list) - set(new_seats_list)
    # - Reservar nuevos asientos que se agregaron
    seats_to_reserve = set(new_seats_list) - set(old_seats_list)

    try:
        for seat_id in seats_to_free:
            update_seat_state(seat_id, False)
        for seat_id in seats_to_reserve:
            update_seat_state(seat_id, True)
    except Exception as e:
        return jsonify({'error': 'Error al actualizar estado de asientos: ' + str(e)}), 500

    # Actualizar reserva
    update_expression_parts = []
    expression_attribute_values = {}

    if new_function_id != existing_reservation.function_id:
        update_expression_parts.append("function_id = :f")
        expression_attribute_values[":f"] = new_function_id
    if new_seats_str != old_seats_str:
        update_expression_parts.append("seats_selected = :s")
        expression_attribute_values[":s"] = new_seats_str
        update_expression_parts.append("numeber_seats_selected = :n")
        expression_attribute_values[":n"] = new_number
    if new_user_email != existing_reservation.user_email:
        update_expression_parts.append("user_email = :e")
        expression_attribute_values[":e"] = new_user_email

    update_expression = "SET " + ", ".join(update_expression_parts)

    try:
        table_reservations.update_item(
            Key={'reserva_id': reserva_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
    except Exception as e:
        return jsonify({'error': 'Error al actualizar reserva: ' + str(e)}), 500

    # Enviar notificación de correo usando AWS SES
    ses_client = current_app.config['SES_CLIENT']
    function_response = table_functions.get_item(Key={'funcion_id': new_function_id})
    if 'Item' in function_response:
        function = Function.from_item(function_response['Item'])
        movie_response = table_movies.get_item(Key={'pelicula_id': function.movie_id})
        movie_title = movie_response['Item'].get('title') if 'Item' in movie_response else 'Unknown'
        room_response = table_rooms.get_item(Key={'sala_id': function.room_id})
        room_name = room_response['Item'].get('name') if 'Item' in room_response else 'Unknown'
        schedule = function.schedule
    else:
        movie_title = room_name = schedule = 'Unknown'

    subject = "Reserva Actualizada"
    body = (
        f"Su reserva para la película '{movie_title}', en la sala '{room_name}' programada para {schedule} "
        f"ha sido actualizada exitosamente. (ID: {reserva_id})"
    )
    send_email(ses_client, new_user_email, subject, body)

    return jsonify({'message': f'Reserva "{reserva_id}" actualizada exitosamente'}), 200

# Endpoint para eliminar una reserva
@reservation_bp.route('/<string:reserva_id>', methods=['DELETE'])
def delete_reservation(reserva_id):
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table_reservations = dynamo_resource.Table('Reservas')
    table_functions = dynamo_resource.Table('Funciones')

    existing_response = table_reservations.get_item(Key={'reserva_id': reserva_id})
    if 'Item' not in existing_response:
        return jsonify({'error': 'Reserva no encontrada'}), 404
    existing_reservation = Reservation.from_item(existing_response['Item'])
    seats_to_release = [s.strip() for s in existing_reservation.seats_selected.split(',') if s.strip()]
    function_id = existing_reservation.function_id

    function_response = table_functions.get_item(Key={'funcion_id': function_id})
    if 'Item' not in function_response:
        return jsonify({'error': 'Función no encontrada'}), 404
    funcion = Function.from_item(function_response['Item'])
    new_available_seats = funcion.available_seats + existing_reservation.numeber_seats_selected
    try:
        table_functions.update_item(
            Key={'funcion_id': function_id},
            UpdateExpression="SET available_seats = :new",
            ExpressionAttributeValues={':new': new_available_seats}
        )
    except Exception as e:
        return jsonify({'error': 'Error al actualizar función: ' + str(e)}), 500

    # Liberar los asientos asociados marcándolos como is_taken = False
    try:
        for seat_id in seats_to_release:
            update_seat_state(seat_id, False)
    except Exception as e:
        return jsonify({'error': 'Error al liberar asientos: ' + str(e)}), 500

    try:
        table_reservations.delete_item(Key={'reserva_id': reserva_id})
    except Exception as e:
        return jsonify({'error': 'Error al eliminar reserva: ' + str(e)}), 500

    # Enviar notificación de cancelación por correo
    ses_client = current_app.config['SES_CLIENT']
    subject = "Reserva Cancelada"
    body = f"Su reserva (ID: {reserva_id}) ha sido cancelada."
    send_email(ses_client, existing_reservation.user_email, subject, body)

    return jsonify({'message': f'Reserva "{reserva_id}" eliminada exitosamente'}), 200
