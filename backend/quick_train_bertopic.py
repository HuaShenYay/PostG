import os
import json
import random
from app import app
from models import db, Poem
import bertopic_analysis

def quick_train(limit=2000):
    print(f"[QuickTrain] Collecting {limit} poems...")
    # Get from DB for speed
    with app.app_context():
        poems = Poem.query.limit(limit).all()
        docs = [p.content for p in poems]
    
    if not docs:
        print("[Error] No poems in DB.")
        return

    print("[QuickTrain] Training mini BERTopic model...")
    model, topics, probs = bertopic_analysis.train_bertopic_model(docs)
    
    print("[QuickTrain] Saving model...")
    bertopic_analysis.save_bertopic_model(model)
    
    print("[QuickTrain] Updating DB tags...")
    with app.app_context():
        all_poems = Poem.query.all()
        for p in all_poems:
            tid, tname = bertopic_analysis.predict_topic(p.content, model)
            p.Bertopic = tname
            label = bertopic_analysis.generate_real_topic(p.content)
            keywords = bertopic_analysis.get_individual_keywords(p.content, top_k=4)
            p.Real_topic = f"{label}-{keywords}" if keywords and keywords not in {"未知", "未分类"} else label
        db.session.commit()
    print("[Success] System is now functional with Mini-Model.")

if __name__ == '__main__':
    quick_train()
