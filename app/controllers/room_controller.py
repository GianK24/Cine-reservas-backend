from flask import Blueprint, request, jsonify, current_app
from app.models.room import Room

room_bp = Blueprint('rooms', __name__)

# Endpoint para obtener todas las salas
@room_bp.route('/', methods=['GET'])
def get_rooms():
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table = dynamo_resource.Table('Salas')
    response = table.scan()
    rooms = [Room.from_item(item).to_item() for item in response.get('Items', [])]
    return jsonify(rooms), 200

# Endpoint para registrar una nueva sala
@room_bp.route('/', methods=['POST'])
def add_room():
    data = request.get_json()
    room = Room(
        name=data.get('name'),
        capacity=data.get('capacity')
    )
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table = dynamo_resource.Table('Salas')
    table.put_item(Item=room.to_item())
    return jsonify(room.to_item()), 201

# Endpoint para actualizar una sala existente
@room_bp.route('/<string:sala_id>', methods=['PUT'])
def update_room(sala_id):
    data = request.get_json()
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table = dynamo_resource.Table('Salas')
    
    update_expression = "SET #n = :n, capacity = :c"
    expression_attribute_values = {
        ':n': data.get('name'),
        ':c': data.get('capacity')
    }
    # Usamos un alias para el atributo name, ya que "name" es una palabra reservada en DynamoDB
    expression_attribute_names = {
        "#n": "name"
    }
    
    try:
        table.update_item(
            Key={'sala_id': sala_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names
        )
        return jsonify({'message': f'Sala "{sala_id}" actualizada exitosamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint para eliminar una sala
@room_bp.route('/<string:sala_id>', methods=['DELETE'])
def delete_room(sala_id):
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table = dynamo_resource.Table('Salas')
    
    try:
        table.delete_item(Key={'sala_id': sala_id})
        return jsonify({'message': f'Sala "{sala_id}" eliminada exitosamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500