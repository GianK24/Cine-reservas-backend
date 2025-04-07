# Backend para Sistema de Reservas de Cine

Este proyecto es un backend en Python utilizando **Flask** y **AWS DynamoDB**, diseñado para gestionar salas, películas, funciones y reservas de un cine.

## Tecnologías utilizadas

- Python 3.10+
- Flask
- Boto3 (para interactuar con AWS DynamoDB y SES)
- DynamoDB (NoSQL)
- Amazon SES (para enviar correos electrónicos)

---

## Instalación y ejecución local

En este momento el codigo esta para correr en blender, pero si quiere correrlo de manera local modifique el archivo run.py con el siguiente contenido:
```bash
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
```

### 1. Clona el repositorio

```bash
git clone https://github.com/GianK24/Cine-reservas-backend.git
cd Cine-reservas-backend
```

### 2. Crea y activa un entorno virtual (opcional pero recomendado)

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate or .\.venv\Scripts\Activate
```

### 3. Instala las dependencias

```bash
pip install -r requirements.txt
```

### 4. Configura tus variables de entorno

Crea un archivo `.env` en la raíz con el siguiente contenido:

```env
AWS_ACCESS_KEY_ID=tu-access-key # Por cuestiones de segurirad no estan las key en este README
AWS_SECRET_ACCESS_KEY=tu-secret-key # Por cuestiones de segurirad no estan las key en este README
AWS_REGION = us-east-2
SES_SENDER_EMAIL = reservascine@gmail.com
```

### 5. Ejecuta la aplicación

```bash
python app.py
```

La app estará corriendo en: [http://localhost:5000](http://localhost:5000)

---

## Despliegue en Render (o plataformas similares)

### Requisitos:

- En el archivo principal (`run.py`) asegúrate de tener:

```python
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
```

### Variables de entorno necesarias en Render, estas estan cargadas en el web service ya desplegado:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

---

## Pruebas con Postman

Puede utilizar **Postman** para probar los endpoints del sistema de reservas. Se incluye una colección exportada con las peticiones ya configuradas.

#### Cómo importar y usar la colección en Postman:
1. Abre Postman.
2. En el panel lateral izquierdo, haz clic en "Collections".
3. Haz clic en el botón "Import" (esquina superior izquierda).
4. Selecciona la pestaña "Upload Files".
5. Busca y selecciona el archivo "Cine reserva.postman_collection.json" incluido en este repositorio.
6. Haz clic en "Import".

La colección aparecerá en tu lista. Desde allí podrás ejecutar todas las peticiones disponibles: CRUD de salas, películas, funciones, reservas.

---

## Estructura del proyecto

```bash
.
├── app/
│   ├── controllers/
│   │   ├── function_controller.py
│   │   ├── movie_controller.py
│   │   ├── reservation_controller.py
│   │   ├── room_controller.py
│   ├── models/
│   │   ├── function.py
│   │   ├── movie.py
│   │   ├── reservation.py
│   │   ├── room.py
│   ├── services/
│   │   ├── email_service.py
│   └── __init__.py
├── run.py
├── requirements.txt
├── Cine reserva.postman_collection.json
├── README.md
└── .env
```
