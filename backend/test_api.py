#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_global_apis():
    base_url = "http://127.0.0.1:5000"
    
    print("测试全局分析API端点...")
    
    # 测试全站统计
    try:
        response = requests.get(f"{base_url}/api/global/stats")
        print(f"✅ 全站统计API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   用户数: {data.get('totalUsers', 0)}")
            print(f"   诗歌数: {data.get('totalPoems', 0)}")
            print(f"   评论数: {data.get('totalReviews', 0)}")
    except Exception as e:
        print(f"❌ 全站统计API失败: {e}")
    
    # 测试热门诗歌
    try:
        response = requests.get(f"{base_url}/api/global/popular-poems")
        print(f"✅ 热门诗歌API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   返回 {len(data)} 首诗歌")
    except Exception as e:
        print(f"❌ 热门诗歌API失败: {e}")
    
    # 测试主题分布
    try:
        response = requests.get(f"{base_url}/api/global/theme-distribution")
        print(f"✅ 主题分布API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   返回 {len(data)} 个主题")
    except Exception as e:
        print(f"❌ 主题分布API失败: {e}")
    
    # 测试朝代分布
    try:
        response = requests.get(f"{base_url}/api/global/dynasty-distribution")
        print(f"✅ 朝代分布API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   返回 {len(data)} 个朝代")
    except Exception as e:
        print(f"❌ 朝代分布API失败: {e}")
    
    # 测试趋势数据
    try:
        response = requests.get(f"{base_url}/api/global/trends")
        print(f"✅ 趋势数据API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"   返回 {len(data)} 天的数据")
                if data:
                    last = data[-1]
                    print(f"   最新: {last.get('date', 'N/A')} = {last.get('count', 0)}")
            else:
                print(f"   返回 {len(data.get('dates', []))} 天的数据")
    except Exception as e:
        print(f"❌ 趋势数据API失败: {e}")
    
    # 测试词云数据
    try:
        response = requests.get(f"{base_url}/api/global/wordcloud")
        print(f"✅ 词云数据API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   返回 {len(data)} 个词汇")
    except Exception as e:
        print(f"❌ 词云数据API失败: {e}")

if __name__ == '__main__':
    test_global_apis()
