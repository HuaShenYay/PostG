#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def add_theme_category_field():
    """手动添加theme_category字段"""
    with app.app_context():
        try:
            # 添加theme_category字段
            db.session.execute(text("ALTER TABLE poems ADD COLUMN theme_category VARCHAR(50)"))
            db.session.commit()
            print("✅ 成功添加theme_category字段")
            
            # 为现有诗歌设置默认主题分类
            db.session.execute(text("UPDATE poems SET theme_category = '山水田园' WHERE theme_category IS NULL"))
            db.session.commit()
            print("✅ 为现有诗歌设置默认主题分类")
            
        except Exception as e:
            print(f"❌ 添加字段失败: {e}")
            db.session.rollback()

if __name__ == '__main__':
    print("添加theme_category字段...")
    add_theme_category_field()
    print("\n完成！")
