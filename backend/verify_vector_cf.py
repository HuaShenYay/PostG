from bertopic_analysis import load_bertopic_model, get_document_vector
import numpy as np
from app import app
from recommendation_update import IncrementalRecommender
from models import User

def verify_vector_cf():
    print("="*50)
    print("Topic Vector CF Verification")
    print("="*50)
    
    # 1. Test Model Loading & Vector Extraction
    print("[1] Testing Model & Vectors...")
    model = load_bertopic_model()
    if not model:
        print("[Fail] Model loading failed!")
        return
    
    text1 = "明月几时有，把酒问青天"
    text2 = "床前明月光，疑是地上霜"
    
    vec1 = get_document_vector(text1, model)
    vec2 = get_document_vector(text2, model)
    
    if vec1 is not None and vec2 is not None:
        print(f"   [Success] Vectors generated. Shape: {vec1.shape}")
        # Test similarity
        from sklearn.metrics.pairwise import cosine_similarity
        sim = cosine_similarity([vec1], [vec2])[0][0]
        print(f"   [Info] Similarity between two moon poems: {sim:.4f}")
    else:
        print("[Fail] Vector generation failed!")
        return

    # 2. Test Recommendation Logic
    print("\n[2] Testing Recommender...")
    with app.app_context():
        recommender = IncrementalRecommender()
        
        # Check matrix build
        if recommender.topic_matrix is not None:
            print(f"   [Success] Topic Matrix built. Shape: {recommender.topic_matrix.shape}")
        else:
            print("[Fail] Topic Matrix build failed!")
            return
            
        # Test recommendation for a user
        user = User.query.first()
        if user:
            print(f"   [Test] Recommendation for user: {user.username} (ID: {user.id})")
            recs = recommender.get_new_poems_for_user(user.id, limit=5)
            print(f"   [Result] Got {len(recs)} recommendations:")
            for p in recs:
                print(f"     - {p.title} (Topic: {p.LDA_topic})")
        else:
            print("   [Skip] No users found for testing.")

    print("\n[Done] Verification finalized.")

if __name__ == '__main__':
    verify_vector_cf()
