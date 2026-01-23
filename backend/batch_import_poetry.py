#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量导入诗歌数据

从 chinese-poetry 目录导入不同朝代的诗歌，目标：将数据库从 366 首增加到约 1000 首

导入计划:
- 宋词三百首: 280 首 (宋)
- 曹操诗集: 26 首 (汉末/三国)
- 元曲: 328 首 (元)
- 总计: 634 首 -> 达到约 1000 首
"""

import json
import os
from datetime import datetime

from app import app
from models import db, Poem

# 使用绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'chinese-poetry')


def load_json_file(filepath):
    """加载 JSON 文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def import_song_ci():
    """导入宋词三百首"""
    filepath = os.path.join(DATA_DIR, '宋词', '宋词三百首.json')
    print(f"\n📖 导入宋词: {filepath}")
    
    data = load_json_file(filepath)
    imported = 0
    
    for item in data:
        # 检查是否已存在
        existing = Poem.query.filter_by(title=item.get('rhythmic', '')).first()
        if existing:
            continue
        
        # 合并段落
        content = '\n'.join(item.get('paragraphs', []))
        
        poem = Poem(
            title=item.get('rhythmic', '无题'),
            author=item.get('author', '未知'),
            content=content,
            dynasty='宋',
            tonal_summary=f"词牌: {item.get('rhythmic', '')}",
            created_at=datetime.utcnow()
        )
        
        db.session.add(poem)
        imported += 1
    
    db.session.commit()
    print(f"  ✅ 成功导入 {imported} 首宋词")
    return imported


def import_caocao():
    """导入曹操诗集"""
    filepath = os.path.join(DATA_DIR, '曹操诗集', 'caocao.json')
    print(f"\n📖 导入曹操诗集: {filepath}")
    
    data = load_json_file(filepath)
    imported = 0
    
    for item in data:
        # 检查是否已存在
        existing = Poem.query.filter_by(title=item.get('title', '')).first()
        if existing:
            continue
        
        # 合并段落
        content = '\n'.join(item.get('paragraphs', []))
        
        poem = Poem(
            title=item.get('title', '无题'),
            author='曹操',
            content=content,
            dynasty='汉末',
            tonal_summary="古体诗",
            created_at=datetime.utcnow()
        )
        
        db.session.add(poem)
        imported += 1
    
    db.session.commit()
    print(f"  ✅ 成功导入 {imported} 首曹操诗")
    return imported


def import_yuanqu(limit=328):
    """导入元曲（限制数量）"""
    filepath = os.path.join(DATA_DIR, '元曲', 'yuanqu.json')
    print(f"\n📖 导入元曲: {filepath} (限制 {limit} 首)")
    
    data = load_json_file(filepath)
    imported = 0
    
    for item in data[:limit]:
        # 提取曲牌名作为标题
        title = item.get('title', '无题')
        # 曲牌名通常在标题中，如 "诈妮子调风月・仙吕/点绛唇"
        if '・' in title:
            title = title.split('・')[1] if title.split('・')[1] else title
        
        # 检查是否已存在
        existing = Poem.query.filter_by(title=title, author=item.get('author', '')).first()
        if existing:
            continue
        
        # 合并段落
        content = '\n'.join(item.get('paragraphs', []))
        
        poem = Poem(
            title=title,
            author=item.get('author', '未知'),
            content=content,
            dynasty='元',
            tonal_summary=f"曲牌: {title}",
            created_at=datetime.utcnow()
        )
        
        db.session.add(poem)
        imported += 1
    
    db.session.commit()
    print(f"  ✅ 成功导入 {imported} 首元曲")
    return imported


def main():
    """主函数"""
    print("=" * 60)
    print("批量导入诗歌数据")
    print("=" * 60)
    
    # 先获取当前数量
    with app.app_context():
        current_count = Poem.query.count()
        print(f"\n📊 当前数据库诗歌总数: {current_count} 首")
        
        # 统计各朝代分布
        from collections import Counter
        dynasties = Counter([p.dynasty for p in Poem.query.all()])
        print("当前朝代分布:")
        for d, c in sorted(dynasties.items(), key=lambda x: -x[1]):
            print(f"  {d}: {c} 首")
    
    print("\n" + "=" * 60)
    print("开始导入...")
    print("=" * 60)
    
    total_imported = 0
    
    with app.app_context():
        # 1. 导入曹操诗集（26首，汉末）
        total_imported += import_caocao()
        
        # 2. 导入宋词三百首（280首，宋）
        total_imported += import_song_ci()
        
        # 3. 导入元曲（328首，元）
        total_imported += import_yuanqu(limit=328)
        
        # 统计结果
        print("\n" + "=" * 60)
        print("导入完成！")
        print("=" * 60)
        
        new_count = Poem.query.count()
        print(f"\n📊 导入后诗歌总数: {new_count} 首")
        print(f"📈 新增诗歌数量: {new_count - current_count} 首")
        
        # 新的朝代分布
        dynasties = Counter([p.dynasty for p in Poem.query.all()])
        print("\n新的朝代分布:")
        for d, c in sorted(dynasties.items(), key=lambda x: -x[1]):
            print(f"  {d}: {c} 首")


if __name__ == '__main__':
    main()
