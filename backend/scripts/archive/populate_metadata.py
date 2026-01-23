import sys
import os
import random
from datetime import datetime, timedelta
import re

# Add path to import app and models
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
from app import app
from models import db, Review, Poem

def populate_metadata():
    print(">>> Starting metadata population...")
    
    with app.app_context():
        # 1. Backfill Review Timestamps
        reviews = Review.query.all()
        print(f"Found {len(reviews)} reviews to check for timestamps.")
        
        updated_reviews = 0
        now = datetime.utcnow()
        
        # Distribution profile for mock times: 
        # heavily weighted towards "recently" (last 1-30 days) for better chart visuals
        for r in reviews:
            if not r.created_at:
                # Random time within last 30 days
                days_ago = random.expovariate(1.0/10) # Exponential distribution
                days_ago = min(days_ago, 60) # Cap at 60 days
                
                # Assign specific hour slots to simulate "reading rhythm"
                # Peak times: 12-13 (Lunch), 20-23 (Night)
                hour_choice = random.choices(
                    [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],
                    weights=[5,2,1,0,0,1,2,5,10,15,10,5,20,15,10,5,5,10,15,20,30,40,35,15],
                    k=1
                )[0]
                
                dt = now - timedelta(days=days_ago)
                r.created_at = dt.replace(hour=hour_choice, minute=random.randint(0, 59))
                updated_reviews += 1
        
        print(f"Backfilled timestamps for {updated_reviews} reviews.")
        
        # 2. Populate Poem Rhythm Metadata
        poems = Poem.query.all()
        print(f"Checking {len(poems)} poems for rhythm metadata.")
        
        updated_poems = 0
        
        for p in poems:
            content = p.content.replace('\n', '').replace(' ', '')
            # Simple heuristic for rhythm classification
            
            # Clean punctuation for counting
            cleaned = re.sub(r'[，。！？；]', '', content)
            length = len(cleaned)
            sentences = re.split(r'[，。！？；]', content)
            sentences = [s for s in sentences if s] # filter empty
            avg_len = sum(len(s) for s in sentences) / len(sentences) if sentences else 0
            
            # Determine Types
            new_rhythm_name = "未知"
            new_rhythm_type = "诗"
            
            # 绝句与律诗判断
            if length == 20 or (len(sentences) == 4 and avg_len == 5):
                new_rhythm_name = "五言绝句"
                new_rhythm_type = "绝句"
            elif length == 28 or (len(sentences) == 4 and avg_len == 7):
                new_rhythm_name = "七言绝句"
                new_rhythm_type = "绝句"
            elif length == 40 or (len(sentences) == 8 and avg_len == 5):
                new_rhythm_name = "五言律诗"
                new_rhythm_type = "律诗"
            elif length == 56 or (len(sentences) == 8 and avg_len == 7):
                new_rhythm_name = "七言律诗"
                new_rhythm_type = "律诗"
            # 词牌判断 (Mock logic - in reality requires title matching)
            elif "·" in p.title: 
                # Usually Title format: 词牌名·题目
                parts = p.title.split('·')
                new_rhythm_name = parts[0]
                new_rhythm_type = "词"
            elif len(p.content) > 60: # Longer usually implies Ci or Gexing
                 new_rhythm_type = "词"
                 new_rhythm_name = "宋词" # Generic fallback
            else:
                new_rhythm_name = "古风"
                new_rhythm_type = "古体诗"
                
            # Update if missing
            if not p.rhythm_name or p.rhythm_name == "Unknown":
                p.rhythm_name = new_rhythm_name
                p.rhythm_type = new_rhythm_type
                updated_poems += 1
                
        print(f"Updated metadata for {updated_poems} poems.")
        
        try:
            db.session.commit()
            print("Database changes committed successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing changes: {e}")

if __name__ == "__main__":
    populate_metadata()
