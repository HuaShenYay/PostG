import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from algorithm_comparison import AlgorithmComparator

class TestAlgorithmComparator(unittest.TestCase):
    def setUp(self):
        self.algo = AlgorithmComparator()
        
        # Mock Data
        self.algo.ratings_df = pd.DataFrame({
            'user_id': [1, 1, 1, 2, 2, 3, 3, 4],
            'poem_id': [101, 102, 103, 101, 102, 102, 103, 104],
            'rating':  [5.0, 3.0, 4.0, 4.0, 3.5, 2.0, 5.0, 4.0]
        })
        
        self.algo.poems_df = pd.DataFrame({
            'id': [101, 102, 103, 104],
            'topic': ['Nature', 'Nature', 'Love', 'War']
        })
        
    def test_split_data(self):
        train_n, test_n = self.algo.split_data(test_size=0.25) # 2 out of 8
        self.assertEqual(train_n + test_n, 8)
        self.assertEqual(test_n, 2)
        
    def test_traditional_cf(self):
        self.algo.split_data(test_size=0.2)
        preds = self.algo.run_traditional_cf(k=2)
        self.assertEqual(len(preds), len(self.algo.test_df))
        # Check predictions range (roughly)
        for p in preds:
            self.assertTrue(0 <= p <= 5.5) # allow some overshoot or 3.0 default
            
    def test_optimized_cf(self):
        self.algo.split_data(test_size=0.2)
        preds = self.algo.run_optimized_cf(k=2, alpha=0.5)
        self.assertEqual(len(preds), len(self.algo.test_df))
        
    def test_evaluate(self):
        preds = [4.0, 3.0, 5.0]
        # Mock test_df for evaluation
        self.algo.test_df = pd.DataFrame({'rating': [4.5, 2.5, 5.0]})
        
        metrics = self.algo.evaluate(preds)
        self.assertIn('rmse', metrics)
        self.assertIn('precision', metrics)
        self.assertIn('f1', metrics)
        self.assertTrue(metrics['rmse'] >= 0)

if __name__ == '__main__':
    unittest.main()
