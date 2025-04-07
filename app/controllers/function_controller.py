from flask import Blueprint, request, jsonify, current_app
from app.models.function import Function

function_bp = Blueprint('functions', __name__)

# Endpoint para obtener todas las funciones
@function_bp.route('/', methods=['GET'])
def get_functions():
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table = dynamo_resource.Table('Funciones')
    response = table.scan()
    functions = [Function.from_item(item).to_item() for item in response.get('Items', [])]
    return jsonify(functions), 200

# Endpoint para registrar una nueva función
@function_bp.route('/', methods=['POST'])
def add_function():
    data = request.get_json()
    room_id = data.get('room_id')
    movie_id = data.get('movie_id')
    schedule = data.get('schedule')

    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table_rooms = dynamo_resource.Table('Salas')
    table_movies = dynamo_resource.Table('Peliculas')
    table_functions = dynamo_resource.Table('Funciones')

    room_response = table_rooms.get_item(Key={'room_id': room_id})
    if 'Item' not in room_response:
        return jsonify({'error': f'Room with room_id "{room_id}" not found'}), 404

    movie_response = table_movies.get_item(Key={'pelicula_id': movie_id})
    if 'Item' not in movie_response:
        return jsonify({'error': f'Movie with movie_id "{movie_id}" not found'}), 404

    room_item = room_response['Item']
    capacity = room_item.get('capacity')
    if capacity is None:
        return jsonify({'error': 'The room does not have a defined capacity'}), 400

    new_function = Function(
        room_id=room_id,
        movie_id=movie_id,
        available_seats=capacity,
        schedule=schedule
    )

    try:
        table_functions.put_item(Item=new_function.to_item())
        return jsonify(new_function.to_item()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint para actualizar una función existente
@function_bp.route('/<string:funcion_id>', methods=['PUT'])
def update_function(funcion_id):
    data = request.get_json()
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table = dynamo_resource.Table('Funciones')
    
    update_expression = "SET room_id = :r, movie_id = :m, available_seats = :a, schedule = :s"
    expression_attribute_values = {
        ':r': data.get('room_id'),
        ':m': data.get('movie_id'),
        ':a': data.get('available_seats'),
        ':s': data.get('schedule')
    }
    
    try:
        table.update_item(
            Key={'funcion_id': funcion_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        return jsonify({'message': f'Function "{funcion_id}" updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint para eliminar una función
@function_bp.route('/<string:funcion_id>', methods=['DELETE'])
def delete_function(funcion_id):
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table = dynamo_resource.Table('Funciones')
    
    try:
        table.delete_item(Key={'funcion_id': funcion_id})
        return jsonify({'message': f'Function "{funcion_id}" deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
