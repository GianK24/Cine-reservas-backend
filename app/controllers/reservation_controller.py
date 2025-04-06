from flask import Blueprint, request, jsonify, current_app
from app.models.reservation import Reservation
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
        movie_id=data.get('movie_id'),
        room_id=data.get('room_id'),
        schedule=data.get('schedule'),
        selected_seats=data.get('selected_seats'),
        user_email=data.get('user_email')
    )
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table = dynamo_resource.Table('Reservas')
    table.put_item(Item=reservation.to_item())

    # Enviar notificación de correo usando AWS SES
    ses_client = current_app.config['SES_CLIENT']
    subject = "Reserva Confirmada"
    body = f"Su reserva (ID: {reservation.reserva_id}) ha sido confirmada."
    send_email(ses_client, reservation.user_email, subject, body)

    return jsonify(reservation.to_item()), 201
