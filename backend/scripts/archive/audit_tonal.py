import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from models import Poem

with app.app_context():
    poems = Poem.query.all()
    empty_ids = []
    for p in poems:
        try:
            data = json.loads(p.tonal_summary)
            if data.get('total', 0) == 0:
                empty_ids.append(p.id)
        except:
            empty_ids.append(p.id)
            
    print(f"POEMS_WITH_ZERO_TOTAL: {len(empty_ids)}")
    if empty_ids:
        print(f"IDs: {empty_ids[:10]}")
