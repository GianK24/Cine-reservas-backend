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
