from flask import Blueprint, request, jsonify, current_app
from app.models.seat import Seat
import string

seats_bp = Blueprint('seats', __name__)

# Crea los asientos para una función
@seats_bp.route('/create/<string:function_id>', methods=['POST'])
def create_seats(function_id):
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table = dynamo_resource.Table('Asientos')

    data = request.get_json()
    total_seats = data.get('total_seats', 50)
    seats_per_row = 10
    row_letters = list(string.ascii_uppercase)

    created_seats = []

    for i in range(total_seats):
        row = row_letters[i // seats_per_row]
        number = (i % seats_per_row) + 1
        seat = Seat(function_id=function_id, row=row, number=number, is_taken=False)
        table.put_item(Item=seat.to_item())
        created_seats.append(seat.to_item())

    return jsonify({
        'message': f'{total_seats} asientos creados para la función {function_id}',
        'seats': created_seats
    }), 201


# Reserva un asiento (marca como ocupado)
@seats_bp.route('/reserve/<string:seat_id>', methods=['PUT'])
def reserve_seat(seat_id):
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table = dynamo_resource.Table('Asientos')

    try:
        response = table.update_item(
            Key={'seat_id': seat_id},
            UpdateExpression="SET is_taken = :val",
            ExpressionAttributeValues={':val': True},
            ReturnValues="UPDATED_NEW"
        )
        return jsonify({
            'message': f'Asiento {seat_id} reservado exitosamente',
            'seat': response['Attributes']
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Obtiene los asientos de una función
@seats_bp.route('/function/<string:function_id>', methods=['GET'])
def get_seats_by_function(function_id):
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table = dynamo_resource.Table('Asientos')

    response = table.scan(
        FilterExpression='function_id = :fid',
        ExpressionAttributeValues={':fid': function_id}
    )
    seats = [Seat.from_item(item).to_item() for item in response.get('Items', [])]
    return jsonify(seats), 200


# Elimina todos los asientos de una función
@seats_bp.route('/function/<string:function_id>', methods=['DELETE'])
def delete_seats_by_function(function_id):
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table = dynamo_resource.Table('Asientos')

    response = table.scan(
        FilterExpression='function_id = :fid',
        ExpressionAttributeValues={':fid': function_id}
    )

    items = response.get('Items', [])
    for item in items:
        table.delete_item(Key={'seat_id': item['seat_id']})

    return jsonify({'message': f'Todos los asientos de la función {function_id} han sido eliminados.'}), 200
