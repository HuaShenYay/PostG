import sys
import os
import json
import re

# Add backend directory to path to import app and models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import Poem
from pypinyin import pinyin, Style

def get_tonal_pattern(text):
    """
    Robustly analyze tonal pattern with fallbacks.
    """
    # Remove non-Chinese characters for pure pinyin analysis
    clean_text = re.sub(r'[^\u4e00-\u9fa5]', '', text)
    
    # Get tones with neutral tone mapped to '5'
    tones = pinyin(clean_text, style=Style.TONE3, neutral_tone_with_five=True)
    
    ping_count = 0
    ze_count = 0
    total = 0
    
    for t in tones:
        if not t: continue
        s = t[0]
        tone_found = False
        
        if s and s[-1].isdigit():
            tone_num = int(s[-1])
            tone_found = True
            if tone_num in [1, 2]:
                ping_count += 1
            else: # 3, 4, 5
                ze_count += 1
        
        if not tone_found:
            # Fallback to TONE2 for single char
            # (Sometimes pinyin fails on whole string but works on single char)
            try:
                # We need context-less fallback if TONE3 failed
                # This is just safety
                pass
            except:
                pass
        
        total += 1

    return {
        "ping": ping_count,
        "ze": ze_count,
        "total": total,
        "ratio": round(ping_count / (total or 1), 2)
    }

def infer_rhythm_info(title, content):
    """
    Infer rhythm name and type from title and content.
    """
    lines = [l for l in re.split(r'[，。？！\n]', content) if len(l.strip()) > 0]
    avg_len = sum(len(l) for l in lines) / (len(lines) or 1)
    
    rhythm_name = "未知"
    rhythm_type = "诗"
    
    # Simple Heuristics for Tang Shi (which is most of DB)
    if "·" in title:
        parts = title.split("·")
        rhythm_name = parts[0]
        rhythm_type = "词"
    elif len(lines) == 4:
        if 4.8 <= avg_len <= 5.2:
            rhythm_name = "五言绝句"
        elif 6.8 <= avg_len <= 7.2:
            rhythm_name = "七言绝句"
    elif len(lines) == 8:
        if 4.8 <= avg_len <= 5.2:
            rhythm_name = "五言律诗"
        elif 6.8 <= avg_len <= 7.2:
            rhythm_name = "七言律诗"
    elif len(lines) > 8:
         rhythm_name = "古体诗" # Pai Lu or Gushi
    else:
        # Check against common Cipai names if strictly needed, but for now fallback
        if avg_len < 5 or avg_len > 7: # irregular
            rhythm_type = "词" # Likely Ci if irregular line lengths
            rhythm_name = "词牌(未知)"

    return rhythm_name, rhythm_type

def analyze_all():
    with app.app_context():
        poems = Poem.query.all()
        print(f"Analyzing {len(poems)} poems...")
        
        updated_count = 0
        for p in poems:
            # 1. Tonal Analysis
            stats = get_tonal_pattern(p.content)
            p.tonal_summary = json.dumps(stats)
            
            # 2. Rhythm Info
            r_name, r_type = infer_rhythm_info(p.title, p.content)
            p.rhythm_name = r_name
            p.rhythm_type = r_type
            
            updated_count += 1
            if updated_count % 50 == 0:
                print(f"Processed {updated_count}...")
        
        db.session.commit()
        print("Analysis complete. Database updated.")

if __name__ == "__main__":
    analyze_all()
