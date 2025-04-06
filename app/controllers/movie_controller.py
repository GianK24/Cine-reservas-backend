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
