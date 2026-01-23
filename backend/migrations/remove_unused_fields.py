#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库字段清理迁移脚本

功能：
1. 从 poems 表中删除未使用的字段
2. 这些字段在 2024-01-24 的代码清理中被注释掉

被删除的字段：
- translation
- appreciation
- author_bio
- notes
- rhythm_name
- rhythm_type
- tags
- difficulty_level
- theme_category

使用方法：
    python migrations/remove_unused_fields.py

注意：
1. 执行前请备份数据库
2. 此操作不可逆，建议在测试环境先验证
3. 字段数据将被永久删除
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from config import Config
from models import db
from sqlalchemy import text


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app


def remove_unused_fields():
    """删除 poems 表中未使用的字段"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("开始清理数据库未使用字段")
        print("=" * 60)
        print()
        
        # 要删除的字段列表
        fields_to_remove = [
            'translation',
            'appreciation',
            'author_bio',
            'notes',
            'rhythm_name',
            'rhythm_type',
            'tags',
            'difficulty_level',
            'theme_category'
        ]
        
        # 检查字段是否存在
        print("检查字段是否存在...")
        existing_fields = []
        missing_fields = []
        
        for field in fields_to_remove:
            result = db.session.execute(
                text(f"SHOW COLUMNS FROM poems LIKE '{field}'")
            ).fetchone()
            
            if result:
                existing_fields.append(field)
                print(f"  ✓ {field} - 存在，将被删除")
            else:
                missing_fields.append(field)
                print(f"  ✗ {field} - 不存在，跳过")
        
        print()
        print(f"将删除 {len(existing_fields)} 个字段")
        print(f"跳过 {len(missing_fields)} 个字段（已不存在）")
        print()
        
        if not existing_fields:
            print("没有需要删除的字段，任务完成")
            return True
        
        # 确认删除
        print("⚠️  警告：此操作将永久删除以下数据：")
        for field in existing_fields:
            count = db.session.execute(
                text(f"SELECT COUNT(*) FROM poems WHERE {field} IS NOT NULL AND {field} != ''")
            ).scalar()
            print(f"   - {field}: {count} 条非空数据")
        print()
        
        # 执行删除
        print("正在删除字段...")
        for field in existing_fields:
            try:
                db.session.execute(text(f"ALTER TABLE poems DROP COLUMN {field}"))
                db.session.commit()
                print(f"  ✓ {field} - 删除成功")
            except Exception as e:
                db.session.rollback()
                print(f"  ✗ {field} - 删除失败: {e}")
        
        print()
        print("=" * 60)
        print("数据库字段清理完成")
        print("=" * 60)
        
        return True


if __name__ == '__main__':
    try:
        remove_unused_fields()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)
