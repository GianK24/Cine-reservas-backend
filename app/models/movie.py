import uuid

class Movie:
    def __init__(self, title, genre, duration, rating, pelicula_id=None):
        self.pelicula_id = pelicula_id or str(uuid.uuid4())
        self.title = title
        self.genre = genre
        self.duration = duration
        self.rating = rating

    def to_item(self):
        return {
            'pelicula_id': self.pelicula_id,
            'title': self.title,
            'genre': self.genre,
            'duration': self.duration,
            'rating': self.rating
        }

    @staticmethod
    def from_item(item):
        return Movie(
            pelicula_id=item.get('pelicula_id'),
            title=item.get('title'),
            genre=item.get('genre'),
            duration=item.get('duration'),
            rating=item.get('rating')
        )
