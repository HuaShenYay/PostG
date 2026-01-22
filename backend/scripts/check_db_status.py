import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from models import Poem

with app.app_context():
    total = Poem.query.count()
    analyzed = Poem.query.filter(Poem.tonal_summary != None).count()
    un_analyzed = Poem.query.filter(Poem.tonal_summary == None).all()
    
    print(f"Total poems: {total}")
    print(f"Poems with tonal_summary: {analyzed}")
    print(f"Poems missing tonal_summary: {total - analyzed}")
    
    if un_analyzed:
        print("\nSample missing poems:")
        for p in un_analyzed[:5]:
            print(f"- ID: {p.id}, Title: {p.title}")
