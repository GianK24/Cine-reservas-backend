import uuid

class Function:
    def __init__(self, room_id, movie_id, available_seats, schedule, funcion_id=None):
        self.funcion_id = funcion_id or str(uuid.uuid4())
        self.room_id = room_id
        self.movie_id = movie_id
        self.available_seats = available_seats
        self.schedule = schedule

    def to_item(self):
        return {
            'funcion_id': self.funcion_id,
            'room_id': self.room_id,
            'movie_id': self.movie_id,
            'available_seats': self.available_seats,
            'schedule': self.schedule
        }

    @staticmethod
    def from_item(item):
        return Function(
            room_id=item.get('room_id'),
            movie_id=item.get('movie_id'),
            available_seats=item.get('available_seats'),
            schedule=item.get('schedule'),
            funcion_id=item.get('funcion_id')
        )
