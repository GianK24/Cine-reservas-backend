import uuid

class Reservation:
    def __init__(self, function_id, seats_selected, numeber_seats_selected, user_email, reserva_id=None):
        self.reserva_id = reserva_id or str(uuid.uuid4())
        self.function_id = function_id
        self.seats_selected = seats_selected
        self.numeber_seats_selected = numeber_seats_selected
        self.user_email = user_email

    def to_item(self):
        return {
            'reserva_id': self.reserva_id,
            'function_id': self.function_id,
            'seats_selected': self.seats_selected,
            'numeber_seats_selected': self.numeber_seats_selected,
            'user_email': self.user_email
        }

    @staticmethod
    def from_item(item):
        return Reservation(
            function_id=item.get('function_id'),
            seats_selected=item.get('seats_selected'),
            numeber_seats_selected=item.get('numeber_seats_selected'),
            user_email=item.get('user_email'),
            reserva_id=item.get('reserva_id')
        )
