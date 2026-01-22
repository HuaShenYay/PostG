import sys
import os
import json
import re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from models import Poem
from pypinyin import pinyin, Style

def get_robust_tonal(text):
    clean = re.sub(r'[^\u4e00-\u9fa5]', '', text)
    if not clean: return {"ping": 0, "ze": 0, "total": 0, "ratio": 0}
    
    tones = pinyin(clean, style=Style.TONE3, neutral_tone_with_five=True)
    ping = 0
    ze = 0
    for t in tones:
        s = t[0]
        if s and s[-1].isdigit():
            n = int(s[-1])
            if n in [1, 2]: ping += 1
            else: ze += 1
        else:
            # TONE2 Fallback
            s2 = pinyin(s if s else ' ', style=Style.TONE2)[0][0]
            if s2 and s2[-1].isdigit():
                n2 = int(s2[-1])
                if n2 in [1, 2]: ping += 1
                else: ze += 1
    
    total = len(clean)
    return {"ping": ping, "ze": ze, "total": total, "ratio": round(ping/max(1, total), 2)}

with app.app_context():
    poems = Poem.query.all()
    print(f"Starting final sweep of {len(poems)} poems...")
    for p in poems:
        p.tonal_summary = json.dumps(get_robust_tonal(p.content))
    db.session.commit()
    print("Database fully synchronized with robust tonal data.")
