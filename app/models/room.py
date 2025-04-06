import uuid

class Room:
    def __init__(self, name, capacity, sala_id=None):
        self.sala_id = sala_id or str(uuid.uuid4())
        self.name = name
        self.capacity = capacity

    def to_item(self):
        return {
            'sala_id': self.sala_id,
            'name': self.name,
            'capacity': self.capacity
        }

    @staticmethod
    def from_item(item):
        return Room(
            sala_id=item.get('sala_id'),
            name=item.get('name'),
            capacity=item.get('capacity')
        )
