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
    
    # Usamos alias para 'duration' porque es una palabra reservada
    update_expression = "SET genre = :g, #d = :d, rating = :r"
    expression_attribute_values = {
        ':g': data.get('genre'),
        ':d': data.get('duration'),
        ':r': data.get('rating')
    }
    expression_attribute_names = {
        "#d": "duration"
    }
    
    try:
        table.update_item(
            Key={'pelicula_id': pelicula_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names
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
