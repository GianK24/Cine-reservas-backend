from flask import Blueprint, request, jsonify, current_app
from app.models.movie import Movie

movie_bp = Blueprint('movies', __name__)

# Endpoint para obtener todas las películas
@movie_bp.route('/', methods=['GET'])
def get_movies():
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table = dynamo_resource.Table('Peliculas')
    response = table.scan()
    movies = [Movie.from_item(item).to_item() for item in response.get('Items', [])]
    return jsonify(movies), 200

# Endpoint para registrar una nueva película
@movie_bp.route('/', methods=['POST'])
def add_movie():
    data = request.get_json()
    movie = Movie(
        title=data.get('title'),
        genre=data.get('genre'),
        duration=data.get('duration'),
        rating=data.get('rating')
    )
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table = dynamo_resource.Table('Peliculas')
    table.put_item(Item=movie.to_item())
    return jsonify(movie.to_item()), 201

# Endpoint para actualizar una película existente
@movie_bp.route('/<string:pelicula_id>', methods=['PUT'])
def update_movie(pelicula_id):
    data = request.get_json()
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table = dynamo_resource.Table('Peliculas')
    
    update_expression_parts = []
    expression_attribute_values = {}
    expression_attribute_names = {}

    if 'genre' in data:
        update_expression_parts.append("genre = :g")
        expression_attribute_values[":g"] = data['genre']
    if 'duration' in data:
        update_expression_parts.append("#d = :d")
        expression_attribute_values[":d"] = data['duration']
        expression_attribute_names["#d"] = "duration"
    if 'rating' in data:
        update_expression_parts.append("rating = :r")
        expression_attribute_values[":r"] = data['rating']

    if not update_expression_parts:
        return jsonify({'message': 'No se proporcionaron campos para actualizar'}), 400

    update_expression = "SET " + ", ".join(update_expression_parts)

    
    try:
        table.update_item(
            Key={'pelicula_id': pelicula_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names if expression_attribute_names else None
        )
        return jsonify({'message': f'Película "{pelicula_id}" actualizada exitosamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint para eliminar una película
@movie_bp.route('/<string:pelicula_id>', methods=['DELETE'])
def delete_movie(pelicula_id):
    dynamo_resource = current_app.config['DYNAMODB_RESOURCE']
    table = dynamo_resource.Table('Peliculas')
    try:
        table.delete_item(Key={'pelicula_id': pelicula_id})
        return jsonify({'message': f'Película "{pelicula_id}" eliminada exitosamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
