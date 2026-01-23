#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, Poem

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def migrate_poem_fields():
    with app.app_context():
        try:
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('poems')]
            
            new_fields = ['likes', 'views', 'shares', 'tags', 'difficulty_level', 'theme_category', 'created_at']
            fields_to_add = [field for field in new_fields if field not in columns]
            
            if fields_to_add:
                print(f"需要添加的字段: {fields_to_add}")
                
                from sqlalchemy import text
                
                if 'likes' in fields_to_add:
                    db.session.execute(text("ALTER TABLE poems ADD COLUMN likes INTEGER DEFAULT 0"))
                    print("✓ 添加 likes 字段")
                
                if 'views' in fields_to_add:
                    db.session.execute(text("ALTER TABLE poems ADD COLUMN views INTEGER DEFAULT 0"))
                    print("✓ 添加 views 字段")
                
                if 'shares' in fields_to_add:
                    db.session.execute(text("ALTER TABLE poems ADD COLUMN shares INTEGER DEFAULT 0"))
                    print("✓ 添加 shares 字段")
                
                if 'tags' in fields_to_add:
                    db.session.execute(text("ALTER TABLE poems ADD COLUMN tags TEXT"))
                    print("✓ 添加 tags 字段")
                
                if 'difficulty_level' in fields_to_add:
                    db.session.execute(text("ALTER TABLE poems ADD COLUMN difficulty_level VARCHAR(10) DEFAULT 'medium'"))
                    print("✓ 添加 difficulty_level 字段")
                
                if 'created_at' in fields_to_add:
                    db.session.execute(text("ALTER TABLE poems ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                    print("✓ 添加 created_at 字段")
                
                db.session.commit()
                print("✅ 数据库字段迁移完成")
            
            else:
                print("✅ 所有必需的字段都已存在")
                
        except Exception as e:
            print(f"❌ 迁移失败: {str(e)}")
            db.session.rollback()

def populate_sample_data():
    with app.app_context():
        try:
            poems = Poem.query.limit(5).all()
            
            for i, poem in enumerate(poems):
                poem.likes = (i + 1) * 100 + 50
                poem.views = (i + 1) * 200 + 100
                poem.shares = (i + 1) * 30 + 10
                poem.difficulty_level = ['easy', 'medium', 'hard'][i % 3]
                poem.theme_category = ['山水田园', '思乡情怀', '豪迈边塞', '爱情闺怨', '哲理说理'][i % 5]
                
                db.session.commit()
                print(f"✅ 更新诗歌 {poem.title} 的数据")
            
            db.session.commit()
            print("✅ 示例数据填充完成")
            
        except Exception as e:
            print(f"❌ 数据填充失败: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    print("开始数据库迁移...")
    migrate_poem_fields()
    print("\n开始填充示例数据...")
    populate_sample_data()
    print("\n迁移完成！")
