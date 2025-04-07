from flask import Flask
from flask_cors import CORS
import boto3
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Configurar boto3 para DynamoDB y SES
    app.config['DYNAMODB_RESOURCE'] = boto3.resource(
        'dynamodb',
        region_name=os.getenv('AWS_REGION'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    app.config['SES_CLIENT'] = boto3.client(
        'ses',
        region_name=os.getenv('AWS_REGION'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )

    # Registrar blueprints
    from app.controllers.movie_controller import movie_bp
    from app.controllers.room_controller import room_bp
    from app.controllers.reservation_controller import reservation_bp
    from app.controllers.function_controller import function_bp

    app.register_blueprint(movie_bp, url_prefix='/movies')
    app.register_blueprint(room_bp, url_prefix='/rooms')
    app.register_blueprint(reservation_bp, url_prefix='/reservations')
    app.register_blueprint(function_bp, url_prefix='/functions')

    return app
