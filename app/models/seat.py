import uuid

class Seat:
    def __init__(self, function_id, row, number, is_taken=False, seat_id=None):
        self.seat_id = seat_id or str(uuid.uuid4())
        self.function_id = function_id
        self.row = row
        self.number = number
        self.is_taken = is_taken

    def to_item(self):
        return {
            'seat_id': self.seat_id,
            'function_id': self.function_id,
            'row': self.row,
            'number': self.number,
            'is_taken': self.is_taken
        }

    @staticmethod
    def from_item(item):
        return Seat(
            seat_id=item.get('seat_id'),
            function_id=item.get('function_id'),
            row=item.get('row'),
            number=item.get('number'),
            is_taken=item.get('is_taken', False)
        )
