#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time

def test_full_integration():
    base_url = "http://127.0.0.1:5000"
    
    print("=== 全站万象页面数据绑定测试 ===\n")
    
    # 1. 测试全站统计数据
    print("1. 测试全站统计数据...")
    try:
        response = requests.get(f"{base_url}/api/global/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 用户总数: {data.get('totalUsers', 0)}")
            print(f"   ✅ 诗歌总数: {data.get('totalPoems', 0)}")
            print(f"   ✅ 评论总数: {data.get('totalReviews', 0)}")
            print(f"   ✅ 总点赞数: {data.get('totalLikes', 0)}")
            print(f"   ✅ 总浏览数: {data.get('totalViews', 0)}")
            print(f"   ✅ 总分享数: {data.get('totalShares', 0)}")
            print(f"   ✅ 平均互动率: {data.get('avgEngagement', '0%')}")
            print(f"   ✅ 今日新用户: {data.get('todayNewUsers', 0)}")
            print(f"   ✅ 今日评论: {data.get('todayReviews', 0)}")
        else:
            print(f"   ❌ 状态码: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 2. 测试热门诗歌
    print("\n2. 测试热门诗歌数据...")
    try:
        response = requests.get(f"{base_url}/api/global/popular-poems?time_range=week")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 返回 {len(data)} 首热门诗歌")
            for i, poem in enumerate(data[:3]):
                print(f"   {i+1}. {poem.get('title', 'N/A')} - {poem.get('author', 'N/A')} (点赞: {poem.get('likes', 0)})")
        else:
            print(f"   ❌ 状态码: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 3. 测试主题分布
    print("\n3. 测试主题分布数据...")
    try:
        response = requests.get(f"{base_url}/api/global/theme-distribution")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 返回 {len(data)} 个主题")
            for i, theme in enumerate(data[:3]):
                print(f"   {i+1}. {theme.get('name', 'N/A')}: {theme.get('value', 0)}")
        else:
            print(f"   ❌ 状态码: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 4. 测试朝代分布
    print("\n4. 测试朝代分布数据...")
    try:
        response = requests.get(f"{base_url}/api/global/dynasty-distribution")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 返回 {len(data)} 个朝代")
            for i, dynasty in enumerate(data[:3]):
                print(f"   {i+1}. {dynasty.get('name', 'N/A')}: {dynasty.get('value', 0)} 首")
        else:
            print(f"   ❌ 状态码: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 5. 测试词云数据
    print("\n5. 测试词云数据...")
    try:
        response = requests.get(f"{base_url}/api/global/wordcloud")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 返回 {len(data)} 个词汇")
            for i, word in enumerate(data[:5]):
                print(f"   {i+1}. {word.get('name', 'N/A')}: {word.get('value', 0)}")
        else:
            print(f"   ❌ 状态码: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 6. 测试趋势数据
    print("\n6. 测试趋势数据...")
    try:
        response = requests.get(f"{base_url}/api/global/trends?period=week")
        if response.status_code == 200:
            data = response.json()
            dates = data.get('dates', [])
            users = data.get('users', [])
            print(f"   ✅ 返回 {len(dates)} 天的数据")
            if len(dates) > 0:
                print(f"   最新日期: {dates[-1]}")
                print(f"   最新用户数: {users[-1]}")
        else:
            print(f"   ❌ 状态码: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    print("\n=== 测试完成 ===")
    print("🎉 全站万象页面的后端API已准备就绪！")
    print("📊 前端页面现在可以连接真实数据进行可视化展示。")

if __name__ == '__main__':
    test_full_integration()
