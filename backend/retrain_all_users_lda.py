#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键重新训练所有用户LDA模型的脚本

功能：
1. 重新训练LDA模型（基于所有评论数据）
2. 为所有评论重新推断主题分布
3. 更新所有用户的偏好画像
4. 保存模型到本地

使用方法：
    python retrain_all_users_lda.py

作者：诗云团队
日期：2024
"""

import sys
import os
import time
import pandas as pd

# 添加后端路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime
from config import Config
from models import db, User, Poem, Review
from lda_analysis import (
    train_lda_model, 
    load_stopwords, 
    preprocess_text, 
    preprocess_text_advanced,
    filter_by_frequency,
    save_lda_model
)
import json
from collections import Counter


def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app


def get_all_reviews_df(app):
    """获取全量评论的DataFrame"""
    with app.app_context():
        sql = text("""
            SELECT r.id as review_id, r.user_id, r.poem_id, r.comment, r.topic_distribution
            FROM reviews r
        """)
        try:
            return pd.read_sql(sql, db.session.connection())
        except Exception:
            return pd.read_sql(sql, db.engine)


def update_user_preference_batch(app, user_ids):
    """批量更新用户偏好画像"""
    with app.app_context():
        updated_count = 0
        
        for user_id in user_ids:
            reviews = Review.query.filter(
                Review.user_id == user_id, 
                Review.topic_distribution != None
            ).all()
            
            if not reviews:
                continue
            
            # 聚合用户的所有评论主题分布
            user_dist = {}
            for r in reviews:
                dist = json.loads(r.topic_distribution)
                for tid, prob in dist.items():
                    user_dist[tid] = user_dist.get(tid, 0) + prob
            
            # 归一化
            total = sum(user_dist.values()) or 1
            preference = []
            for tid, score in user_dist.items():
                preference.append({
                    "topic_id": int(tid),
                    "score": float(score / total)
                })
            
            # 按得分排序
            preference.sort(key=lambda x: x['score'], reverse=True)
            
            # 保存到数据库
            user = User.query.get(user_id)
            if user:
                user.preference_topics = json.dumps(preference)
                db.session.commit()
                updated_count += 1
                print(f"  ✓ 用户 {user.username} (ID:{user_id}) 偏好已更新")
        
        return updated_count


def retrain_all_users_lda():
    """
    一键重新训练所有用户LDA模型
    
    流程：
    1. 加载数据库数据
    2. 重新训练LDA模型
    3. 为所有评论重新推断主题分布
    4. 更新所有用户偏好画像
    5. 保存模型
    """
    print("=" * 60)
    print("🚀 开始一键重新训练所有用户LDA模型")
    print("=" * 60)
    print()
    
    start_time = time.time()
    
    # 1. 创建应用并连接数据库
    print("📦 步骤1: 连接数据库...")
    app = create_app()
    
    with app.app_context():
        try:
            # 测试数据库连接
            db.engine.connect()
            print("  ✅ 数据库连接成功")
        except Exception as e:
            print(f"  ❌ 数据库连接失败: {e}")
            return False
    
    # 2. 获取全量评论数据
    print("\n📚 步骤2: 加载全量评论数据...")
    df_reviews = get_all_reviews_df(app)
    total_reviews = len(df_reviews)
    total_users = df_reviews['user_id'].nunique() if total_reviews > 0 else 0
    
    print(f"  ✅ 加载了 {total_reviews} 条评论")
    print(f"  ✅ 涉及 {total_users} 位用户")
    
    if total_reviews == 0:
        print("  ⚠️  没有评论数据，无需训练")
        return True
    
    # 3. 重新训练LDA模型
    print("\n🎯 步骤3: 重新训练LDA模型...")
    print("  ⏳ 这可能需要一些时间，请耐心等待...")
    
    # 加载停用词
    stopwords = load_stopwords()
    print(f"  📖 加载了 {len(stopwords)} 个停用词")
    
    # 预处理评论
    print("  ✂️ 正在进行文本预处理...")
    tokenized_texts = df_reviews['comment'].apply(
        lambda x: preprocess_text(str(x), stopwords)
    ).tolist()
    
    # 词频过滤
    tokenized_texts, valid_words = filter_by_frequency(
        tokenized_texts, 
        min_freq=2,
        max_doc_ratio=0.8
    )
    
    # 使用高级预处理重新处理
    tokenized_texts = [
        preprocess_text_advanced(str(text), stopwords, valid_words)
        for text in df_reviews['comment']
    ]
    
    print(f"  ✅ 完成预处理，共 {len(tokenized_texts)} 条文本")
    
    # 训练LDA模型
    lda, dictionary, df, topic_keywords = train_lda_model(
        df_reviews, 
        use_advanced_preprocessing=False  # 已经预处理过了
    )
    
    if lda is None:
        print("  ❌ LDA模型训练失败")
        return False
    
    print(f"  ✅ LDA模型训练完成")
    print(f"     - 主题数: {len(topic_keywords)}")
    print(f"     - 词汇表大小: {len(dictionary)}")
    
    # 显示主题关键词
    print("\n📋 主题关键词预览:")
    for topic_id, keywords in topic_keywords.items():
        print(f"  主题 {topic_id}: {', '.join(keywords[:5])}")
    
    # 4. 为所有评论推断主题分布
    print("\n🔄 步骤4: 为所有评论重新推断主题分布...")
    
    with app.app_context():
        all_reviews = Review.query.all()
        processed_count = 0
        
        for r in all_reviews:
            tokens = preprocess_text(str(r.comment), stopwords)
            
            if tokens:
                bow = dictionary.doc2bow(tokens)
                dist = dict(lda[bow])
                r.topic_distribution = json.dumps({str(k): float(v) for k, v in dist.items()})
            else:
                r.topic_distribution = json.dumps({})
            
            processed_count += 1
        
        db.session.commit()
        print(f"  ✅ 已更新 {processed_count}/{len(all_reviews)} 条评论的主题分布")
    
    # 5. 更新所有用户偏好画像
    print("\n👤 步骤5: 更新所有用户偏好画像...")
    
    with app.app_context():
        all_user_ids = [u.id for u in User.query.all()]
        updated_users = update_user_preference_batch(app, all_user_ids)
        print(f"  ✅ 已更新 {updated_users}/{len(all_user_ids)} 位用户的偏好画像")
    
    # 6. 保存模型
    print("\n💾 步骤6: 保存模型到本地...")
    
    try:
        save_lda_model(lda, dictionary, topic_keywords)
        print("  ✅ 模型已保存到 saved_models/ 目录")
    except Exception as e:
        print(f"  ⚠️  模型保存失败: {e}")
    
    # 7. 完成
    elapsed_time = time.time() - start_time
    
    print()
    print("=" * 60)
    print("✅ 一键重新训练完成！")
    print("=" * 60)
    print()
    print("📊 执行摘要:")
    print(f"   - 处理评论数: {total_reviews}")
    print(f"   - 涉及用户数: {total_users}")
    print(f"   - LDA主题数: {len(topic_keywords)}")
    print(f"   - 词汇表大小: {len(dictionary)}")
    print(f"   - 更新用户数: {updated_users}")
    print(f"   - 总耗时: {elapsed_time:.2f} 秒")
    print()
    print("💡 提示: 模型已自动重新加载，下次API调用将使用新模型")
    print()
    
    return True


def main():
    """主函数"""
    try:
        retrain_all_users_lda()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
