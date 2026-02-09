from app import app
from models import Poem
with app.app_context():
    sample = Poem.query.filter(Poem.Bertopic != None).first()
    if sample:
        print(f"Title: {sample.title}")
        print(f"Topic: {sample.Bertopic}")
        print(f"Real_topic: {sample.Real_topic}")
    else:
        print("No tagged poems found.")
