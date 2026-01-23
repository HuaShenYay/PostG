#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, Poem
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def check_and_fix_fields():
    """检查并修复数据库字段问题"""
    with app.app_context():
        try:
            # 检查字段是否存在
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('poems')]
            print(f"当前poems表字段: {columns}")
            
            # 检查是否有诗歌数据
            poems_count = Poem.query.count()
            print(f"诗歌总数: {poems_count}")
            
            # 为现有诗歌填充数据
            if poems_count > 0:
                poems = Poem.query.all()
                for poem in poems:
                    # 检查并设置默认值
                    if not hasattr(poem, 'likes') or poem.likes is None:
                        poem.likes = 0
                    if not hasattr(poem, 'views') or poem.views is None:
                        poem.views = 0
                    if not hasattr(poem, 'shares') or poem.shares is None:
                        poem.shares = 0
                    if not hasattr(poem, 'difficulty_level') or poem.difficulty_level is None:
                        poem.difficulty_level = 'medium'
                    if not hasattr(poem, 'theme_category') or poem.theme_category is None:
                        poem.theme_category = '山水田园'
                    
                    # 设置一些示例数据
                    poem.likes = poem.likes or 100
                    poem.views = poem.views or 200
                    poem.shares = poem.shares or 30
                
                db.session.commit()
                print("✅ 已为现有诗歌填充示例数据")
            
            # 测试查询
            try:
                from sqlalchemy import func
                total_likes = db.session.query(func.sum(Poem.likes)).scalar() or 0
                total_views = db.session.query(func.sum(Poem.views)).scalar() or 0
                total_shares = db.session.query(func.sum(Poem.shares)).scalar() or 0
                
                print(f"✅ 测试查询成功:")
                print(f"   总点赞数: {total_likes}")
                print(f"   总浏览数: {total_views}")
                print(f"   总分享数: {total_shares}")
                
            except Exception as e:
                print(f"❌ 测试查询失败: {e}")
                
        except Exception as e:
            print(f"❌ 检查失败: {e}")
            db.session.rollback()

if __name__ == '__main__':
    print("检查并修复数据库字段...")
    check_and_fix_fields()
    print("\n完成！")
