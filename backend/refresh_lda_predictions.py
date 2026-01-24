from app import app
from models import db, Poem
import lda_analysis
import os

def refresh():
    with app.app_context():
        print("[Refresh] Loading LDA model...")
        lda, dictionary, keywords = lda_analysis.load_lda_model()
        
        if not lda:
            print("[Error] No model found to refresh with.")
            return
            
        print(f"[Refresh] Found model with {len(keywords)} topics.")
        
        poems = Poem.query.all()
        total = len(poems)
        print(f"[Refresh] Updating {total} poems...")
        
        for i, p in enumerate(poems):
            old_topic = p.LDA_topic
            new_topic = lda_analysis.predict_topic(p.content, lda, dictionary, keywords)
            p.LDA_topic = new_topic
            
            if (i+1) % 100 == 0:
                print(f"  - Progress: {i+1}/{total}")
        
        db.session.commit()
        print(f"[Success] Refreshed all {total} poems.")

if __name__ == '__main__':
    refresh()
