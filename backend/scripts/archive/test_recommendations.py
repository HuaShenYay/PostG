import requests
import json
import unittest

BASE_URL = "http://127.0.0.1:5000/api"

class TestPoetryRecommendations(unittest.TestCase):
    
    def test_01_visitor_recommend_one(self):
        """测试访客随机推荐"""
        print("\n[Test 01] Testing visitor random recommendation...")
        response = requests.get(f"{BASE_URL}/recommend_one/访客")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('title', data)
        self.assertIn('content', data)
        self.assertIn('recommend_reason', data)
        print(f"Success: Got poem '{data['title']}' with reason: {data['recommend_reason']}")

    def test_02_diversity_skip_logic(self):
        """测试多样性推荐逻辑（skip_count=5）"""
        print("\n[Test 02] Testing diversity skip logic (skip_count=5)...")
        # 通过 skip_count=5 触发"发现尚未被发现的佳作"逻辑
        response = requests.get(f"{BASE_URL}/recommend_one/访客?skip_count=5")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # 验证推荐理由是否符合预期逻辑
        self.assertEqual(data['recommend_reason'], "为您推荐一首尚未被发现的佳作")
        print(f"Success: Diversity logic triggered. Got unseen poem '{data['title']}'")

    def test_03_personalized_recommendation(self):
        """测试个性化推荐逻辑"""
        # 我们假设用户 'huashenyay' 已经有画像数据
        print("\n[Test 03] Testing personalized recommendation for 'huashenyay'...")
        response = requests.get(f"{BASE_URL}/recommend_one/huashenyay")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('recommend_reason', data)
        # 个性化推荐的理由通常包含 "因您对...感兴趣而荐"
        print(f"Success: Personalized reason: {data['recommend_reason']}")

    def test_04_analysis_api(self):
        """测试单首诗深度分析数据接口"""
        print("\n[Test 04] Testing poem analysis API...")
        # 取第一首诗进行测试
        poem_id = 1
        response = requests.get(f"{BASE_URL}/poem/{poem_id}/analysis")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('matrix', data)
        self.assertIn('rhymes', data)
        self.assertIn('chart_data', data)
        self.assertIn('tonal_sequence', data['chart_data'])
        self.assertIn('sentiment', data['chart_data'])
        print(f"Success: Analysis data retrieved for poem ID {poem_id}")

    def test_05_system_visual_stats(self):
        """测试系统全局统计数据接口（雷达图等）"""
        print("\n[Test 05] Testing global visual stats...")
        response = requests.get(f"{BASE_URL}/visual/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('radar_data', data)
        self.assertIn('sankey_data', data)
        self.assertIn('counts', data)
        print("Success: Global statistics retrieved.")

if __name__ == "__main__":
    unittest.main()
