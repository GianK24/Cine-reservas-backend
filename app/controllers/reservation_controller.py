from flask import Blueprint, request, jsonify, current_app
from app.models.reservation import Reservation
from app.models.function import Function
from app.services.email_service import send_email

reservation_bp = Blueprint('reservations', __name__)

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
        user_email=data.get('user_email')
    )
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table_reservations = dynamo_resource.Table('Reservas')
    table_functions = dynamo_resource.Table('Funciones')
    table_movies = dynamo_resource.Table('Peliculas')
    table_rooms = dynamo_resource.Table('Salas')

    function_response = table_functions.get_item(Key={'funcion_id': reservation.function_id})
    if 'Item' not in function_response:
        return jsonify({'error': 'Función no encontrada'}), 404

    funcion_item = function_response['Item']
    function = Function.from_item(funcion_item)

    if function.asientos_disponibles < reservation.seats_selected:
        return jsonify({'error': 'No hay suficientes asientos disponibles'}), 400

    new_asientos = function.asientos_disponibles - reservation.seats_selected
    try:
        table_functions.update_item(
            Key={'funcion_id': reservation.function_id},
            UpdateExpression="SET asientos_disponibles = :new",
            ExpressionAttributeValues={':new': new_asientos}
        )
    except Exception as e:
        return jsonify({'error': 'Error al actualizar asientos: ' + str(e)}), 500

    try:
        table_reservations.put_item(Item=reservation.to_item())
    except Exception as e:
        return jsonify({'error': 'Error al guardar reserva: ' + str(e)}), 500

    # Enviar notificación de correo usando AWS SES
    ses_client = current_app.config['SES_CLIENT']

    function_response = table_functions.get_item(Key={'funcion_id': reservation.function_id})
    if 'Item' in function_response:
        function = Function.from_item(function_response['Item'])
        # Retrieve movie details
        movie_response = table_movies.get_item(Key={'pelicula_id': function.movie_id})
        movie_title = movie_response['Item'].get('title') if 'Item' in movie_response else 'Unknown'
        # Retrieve room details
        room_response = table_rooms.get_item(Key={'room_id': function.room_id})
        room_name = room_response['Item'].get('name') if 'Item' in room_response else 'Unknown'
        schedule = function.schedule
    else:
        movie_title = room_name = schedule = 'Unknown'

    subject = "Reserva Confirmada"
    body = (
        f"Su reserva para la película '{movie_title}', en la sala '{room_name}' programada para {schedule} ha sido confirmada. (ID: {reservation.reserva_id})"
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
    old_seats = existing_reservation.seats_selected

    new_function_id = data.get('function_id', existing_reservation.function_id)
    new_seats = data.get('seats_selected', old_seats)
    new_user_email = data.get('user_email', existing_reservation.user_email)


    seat_diff = old_seats - new_seats  # Si positivo: se liberaron asientos; si negativo: se requieren más asientos

    function_response = table_functions.get_item(Key={'funcion_id': new_function_id})
    if 'Item' not in function_response:
        return jsonify({'error': 'Función no encontrada'}), 404
    function = Function.from_item(function_response['Item'])
    
    if seat_diff < 0:
        if function.available_seats < abs(seat_diff):
            return jsonify({'error': 'No hay suficientes asientos disponibles para la actualización'}), 400

    new_available_seats = function.available_seats + seat_diff
    try:
        table_functions.update_item(
            Key={'funcion_id': new_function_id},
            UpdateExpression="SET available_seats = :new",
            ExpressionAttributeValues={':new': new_available_seats}
        )
    except Exception as e:
        return jsonify({'error': 'Error al actualizar función: ' + str(e)}), 500

    try:
        update_expression = "SET function_id = :f, seats_selected = :s, user_email = :e"
        expression_attribute_values = {
            ':f': new_function_id,
            ':s': new_seats,
            ':e': new_user_email
        }
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
        # Retrieve movie details
        movie_response = table_movies.get_item(Key={'pelicula_id': function.movie_id})
        movie_title = movie_response['Item'].get('title') if 'Item' in movie_response else 'Unknown'
        # Retrieve room details
        room_response = table_rooms.get_item(Key={'room_id': function.room_id})
        room_name = room_response['Item'].get('name') if 'Item' in room_response else 'Unknown'
        schedule = function.schedule
    else:
        movie_title = room_name = schedule = 'Unknown'

    subject = "Reserva Actualizada"
    body = (
    f"Su reserva para la película '{movie_title}', en la sala '{room_name}' programada para {schedule} ha sido actualizada exitosamente. (ID: {reserva_id})"
    )
    send_email(ses_client, new_user_email, subject, body)

    return jsonify({'message': f'Reserva "{reserva_id}" actualizada exitosamente'}), 200

# Endpoint para eliminar una reserva
@reservation_bp.route('/<string:reserva_id>', methods=['DELETE'])
def delete_reservation(reserva_id):
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table_reservas = dynamo_resource.Table('Reservas')
    table_funciones = dynamo_resource.Table('Funciones')

    existing_response = table_reservas.get_item(Key={'reserva_id': reserva_id})
    if 'Item' not in existing_response:
        return jsonify({'error': 'Reserva no encontrada'}), 404
    existing_reservation = Reservation.from_item(existing_response['Item'])
    seats_to_release = existing_reservation.seats_selected
    function_id = existing_reservation.function_id

    function_response = table_funciones.get_item(Key={'funcion_id': function_id})
    if 'Item' not in function_response:
        return jsonify({'error': 'Función no encontrada'}), 404
    funcion = Function.from_item(function_response['Item'])
    new_available_seats = funcion.available_seats + seats_to_release
    try:
        table_funciones.update_item(
            Key={'funcion_id': function_id},
            UpdateExpression="SET available_seats = :new",
            ExpressionAttributeValues={':new': new_available_seats}
        )
    except Exception as e:
        return jsonify({'error': 'Error al actualizar función: ' + str(e)}), 500

    try:
        table_reservas.delete_item(Key={'reserva_id': reserva_id})
    except Exception as e:
        return jsonify({'error': 'Error al eliminar reserva: ' + str(e)}), 500
    
    # Enviar notificación de correo usando AWS SES
    ses_client = current_app.config['SES_CLIENT']
    subject = "Reserva Cancelada"
    body = f"Su reserva (ID: {reserva_id}) ha sido cancelada."
    send_email(ses_client, existing_reservation.user_email, subject, body)

    return jsonify({'message': f'Reserva "{reserva_id}" eliminada exitosamente'}), 200