import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from models import Poem

with app.app_context():
    total = Poem.query.count()
    full_data = Poem.query.filter(Poem.tonal_summary != None).count()
    no_data = Poem.query.filter(Poem.tonal_summary == None).count()
    print(f"REPORT_START")
    print(f"TOTAL_POEMS: {total}")
    print(f"LOCKED_DATA: {full_data}")
    print(f"MISSING_DATA: {no_data}")
    print(f"REPORT_END")
