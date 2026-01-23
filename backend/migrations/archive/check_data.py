from app import app
from models import Poem
with app.app_context():
    poems = Poem.query.limit(20).all()
    for p in poems:
        print(f"ID: {p.id}, Title: {p.title}, Rhythm: {p.rhythm_name}, Type: {p.rhythm_type}")
