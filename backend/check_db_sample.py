from app import app
from models import Poem
with app.app_context():
    sample = Poem.query.filter(Poem.LDA_topic != None).first()
    if sample:
        print(f"Title: {sample.title}")
        print(f"Topic: {sample.LDA_topic}")
    else:
        print("No tagged poems found.")
