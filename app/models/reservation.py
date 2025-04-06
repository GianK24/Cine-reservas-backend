import uuid

class Reservation:
    def __init__(self, movie_id, room_id, schedule, selected_seats, user_email, reserva_id=None):
        self.reserva_id = reserva_id or str(uuid.uuid4())
        self.movie_id = movie_id
        self.room_id = room_id
        self.schedule = schedule
        self.selected_seats = selected_seats  # Se espera una lista de asientos
        self.user_email = user_email

    def to_item(self):
        return {
            'reserva_id': self.reserva_id,
            'movie_id': self.movie_id,
            'room_id': self.room_id,
            'schedule': self.schedule,
            'selected_seats': self.selected_seats,
            'user_email': self.user_email
        }

    @staticmethod
    def from_item(item):
        return Reservation(
            reserva_id=item.get('reserva_id'),
            movie_id=item.get('movie_id'),
            room_id=item.get('room_id'),
            schedule=item.get('schedule'),
            selected_seats=item.get('selected_seats'),
            user_email=item.get('user_email')
        )
