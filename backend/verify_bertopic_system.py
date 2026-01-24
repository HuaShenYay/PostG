from app import app
from models import db, Poem, User
from bertopic_analysis import load_bertopic_model, predict_topic
from recommendation_update import IncrementalRecommender

def verify():
    print("="*50)
    print("BERTopic System Verification")
    print("="*50)
    
    # 1. Model Check
    print("[1] Checking Model...")
    model = load_bertopic_model()
    if model:
        print(f"   [Success] Model loaded: {type(model)}")
        topic_info = model.get_topic_info()
        print(f"   [Info] Total topics found: {len(topic_info) - 1}") # exclude -1
    else:
        print("   [Fail] Model not found or failed to load.")
        return

    # 2. Prediction Check
    print("\n[2] Checking Prediction...")
    test_text = "明月几时有，把酒问青天。"
    tid, tname = predict_topic(test_text, model)
    print(f"   [Test] Text: {test_text}")
    print(f"   [Result] Topic ID: {tid}, Name: {tname}")
    
    # 3. Database Check
    print("\n[3] Checking Database...")
    with app.app_context():
        total = Poem.query.count()
        tagged = Poem.query.filter(Poem.LDA_topic != None).count()
        print(f"   Total Poems: {total}")
        print(f"   Tagged Poems: {tagged}")
        
        sample = Poem.query.filter(Poem.LDA_topic != None).first()
        if sample:
            print(f"   [Sample] {sample.title} -> {sample.LDA_topic} (ID: {sample.Real_topic})")
        else:
            print("   [Warning] No tagged poems found in DB.")

    # 4. Recommendation Check
    print("\n[4] Checking Recommendation Engine...")
    with app.app_context():
        user = User.query.first()
        if user:
            print(f"   [User] {user.username}")
            recommender = IncrementalRecommender()
            recs = recommender.get_new_poems_for_user(user.id)
            print(f"   [Recs] Generated {len(recs)} recommendations:")
            for p in recs:
                print(f"     - {p.title} ({p.LDA_topic})")
        else:
            print("   [Skip] No users in DB.")

    print("\n[Done] Verification checks completed.")

if __name__ == '__main__':
    verify()
