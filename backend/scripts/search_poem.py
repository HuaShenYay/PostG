import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from models import Poem

with app.app_context():
    print("Searching for '鹿柴'...")
    p1 = Poem.query.filter(Poem.title.like('%鹿柴%')).first()
    if p1:
        print(f"Found: {p1.title} (ID: {p1.id})")
    else:
        print("Not found by '鹿柴'")

    print("\nSearching for '辋川集'...")
    p2 = Poem.query.filter(Poem.title.like('%辋川集%')).first()
    if p2:
        print(f"Found: {p2.title} (ID: {p2.id})")
    else:
        print("Not found by '辋川集'")
        
    total = Poem.query.count()
    print(f"\nTotal poems in DB: {total}")
