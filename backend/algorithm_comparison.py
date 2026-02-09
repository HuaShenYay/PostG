import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import math
from models import db, Review, Poem, User

class AlgorithmComparator:
    def __init__(self):
        self.ratings_df = None
        self.poems_df = None
        self.train_df = None
        self.test_df = None
        self.user_sim_matrix = None
        self.topic_sim_matrix = None
        
    def load_data_from_db(self):
        """Load data from database into pandas DataFrames"""
        # Load Reviews
        reviews = Review.query.with_entities(Review.user_id, Review.poem_id, Review.rating).all()
        self.ratings_df = pd.DataFrame(reviews, columns=['user_id', 'poem_id', 'rating'])
        
        # Load Poems (for content/topic info)
        poems = Poem.query.with_entities(Poem.id, Poem.Bertopic, Poem.Real_topic).all()
        self.poems_df = pd.DataFrame(poems, columns=['id', 'Bertopic', 'Real_topic'])
        
        # Current System Logic: Use Bertopic as the operational topic (optimized CF uses this)
        # Real_topic is ONLY for ground truth reference in other contexts if needed, 
        # but here optimized CF should use the system's actual topic data (Bertopic).
        # However, to simulate "Optimized" vs "Traditional", the Optimized one uses Topics.
        # We use Bertopic as the primary source for the algorithm.
        self.poems_df['topic'] = self.poems_df['Bertopic'].fillna('Unknown')
        
        return len(self.ratings_df)

    def split_data(self, test_size=0.2):
        """Split ratings into train and test sets"""
        if self.ratings_df is None or self.ratings_df.empty:
            raise ValueError("No data loaded")
            
        self.train_df, self.test_df = train_test_split(self.ratings_df, test_size=test_size, random_state=42)
        return len(self.train_df), len(self.test_df)

    def _calculate_user_similarity(self, df):
        """Calculate User-User Similarity Matrix based on Ratings (Pearson)"""
        # Create User-Item Matrix
        user_item_matrix = df.pivot_table(
            index='user_id',
            columns='poem_id',
            values='rating',
            aggfunc='mean'
        ).fillna(0)
        
        # Calculate Cosine Similarity (approx for Pearson if centered, or just use Cosine)
        # Using Cosine on ratings for simplicity and speed in this demo
        sim_matrix = cosine_similarity(user_item_matrix)
        user_ids = user_item_matrix.index
        
        return pd.DataFrame(sim_matrix, index=user_ids, columns=user_ids)

    def _calculate_topic_similarity(self, df):
        """Calculate User-User Similarity based on Topic Preferences"""
        # 1. Merge ratings with poem topics
        merged = df.merge(self.poems_df, left_on='poem_id', right_on='id')
        
        # 2. Build User-Topic Profile (weighted by rating)
        # One-hot encode topics first? Or just aggregate.
        # Let's use a simpler approach: Vector of average rating per topic per user
        user_topic_matrix = merged.pivot_table(index='user_id', columns='topic', values='rating', aggfunc='mean').fillna(0)
        
        # 3. Calculate Similarity
        if user_topic_matrix.empty:
            return pd.DataFrame()
            
        sim_matrix = cosine_similarity(user_topic_matrix)
        user_ids = user_topic_matrix.index
        
        return pd.DataFrame(sim_matrix, index=user_ids, columns=user_ids)

    def run_traditional_cf(self, k=20):
        """
        Run Traditional User-based CF
        Returns: Predictions for test set
        """
        self.user_sim_matrix = self._calculate_user_similarity(self.train_df)
        return self._predict(self.user_sim_matrix, k)

    def run_optimized_cf(self, k=20, alpha=0.7):
        """
        Run Optimized CF (Rating Sim * alpha + Topic Sim * (1-alpha))
        Returns: Predictions for test set
        """
        rating_sim = self._calculate_user_similarity(self.train_df)
        topic_sim = self._calculate_topic_similarity(self.train_df)
        
        # Align indices (ensure both matrices have same users)
        common_users = rating_sim.index.intersection(topic_sim.index)
        rating_sim = rating_sim.loc[common_users, common_users]
        topic_sim = topic_sim.loc[common_users, common_users]
        
        # Fuse similarities
        hybrid_sim = alpha * rating_sim + (1 - alpha) * topic_sim
        
        self.user_sim_matrix = hybrid_sim
        return self._predict(self.user_sim_matrix, k)

    def _predict(self, sim_matrix, k):
        """Generic prediction function using a similarity matrix"""
        predictions = []
        
        # Pre-compute User-Item Matrix for training data
        train_matrix = self.train_df.pivot_table(
            index='user_id',
            columns='poem_id',
            values='rating',
            aggfunc='mean'
        ).fillna(0)
        user_ids = train_matrix.index
        
        for _, row in self.test_df.iterrows():
            user = row['user_id']
            item = row['poem_id']
            
            if user not in sim_matrix.index or item not in train_matrix.columns:
                # Cold start: predict global average or 3.0
                pred = 3.0 
            else:
                # Get K nearest neighbors who rated this item
                # 1. Get all users who rated this item
                rated_users = train_matrix[item][train_matrix[item] > 0].index
                
                # 2. Filter neighbors
                neighbors = sim_matrix.loc[user, rated_users]
                
                # 3. Top K
                k_neighbors = neighbors.nlargest(k)
                
                if k_neighbors.empty or k_neighbors.sum() == 0:
                    pred = 3.0
                else:
                    # Weighted sum
                    # Retrieve ratings for these neighbors
                    neighbor_ratings = train_matrix.loc[k_neighbors.index, item]
                    
                    numerator = np.dot(k_neighbors.values, neighbor_ratings.values)
                    denominator = k_neighbors.abs().sum()
                    
                    pred = numerator / denominator if denominator != 0 else 3.0
            
            predictions.append(pred)
            
        return predictions

    def evaluate(self, predictions, threshold=3.5):
        """Calculate metrics"""
        y_true = self.test_df['rating'].values
        y_pred = np.array(predictions)
        
        # RMSE
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        
        # Classification Metrics (convert ratings to binary Relevance)
        y_true_bin = (y_true >= threshold).astype(int)
        y_pred_bin = (y_pred >= threshold).astype(int)
        
        precision = precision_score(y_true_bin, y_pred_bin, zero_division=0)
        recall = recall_score(y_true_bin, y_pred_bin, zero_division=0)
        f1 = f1_score(y_true_bin, y_pred_bin, zero_division=0)
        
        return {
            "rmse": round(rmse, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4)
        }
