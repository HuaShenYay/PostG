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
from lda_analysis import load_lda_model, predict_topic

# 使用绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'chinese-poetry')

# 加载 LDA 模型用于导入时打标签
LDA_MODEL, LDA_DICT, TOPIC_KW = load_lda_model()

def load_json_file(filepath):
    """加载 JSON 文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def tag_poem(poem_content):
    """为诗歌打上 LDA 标签"""
    if LDA_MODEL:
        return predict_topic(poem_content, LDA_MODEL, LDA_DICT, TOPIC_KW)
    return "未分类"

def import_song_ci():
    """导入宋词三百首"""
    filepath = os.path.join(DATA_DIR, '宋词', '宋词三百首.json')
    print(f"\n[Info] Importing Song Ci: {filepath}")
    
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
            genre_type='词',
            rhythm_name=item.get('rhythmic', ''),
            rhythm_type='宋词',
            LDA_topic=tag_poem(content),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(poem)
        imported += 1
    
    db.session.commit()
    print(f"  [Success] Imported {imported} Song Ci poems")
    return imported

def import_caocao():
    """导入曹操诗集"""
    filepath = os.path.join(DATA_DIR, '曹操诗集', 'caocao.json')
    print(f"\n[Info] Importing Caocao: {filepath}")
    
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
            genre_type='诗',
            rhythm_type='古体诗',
            LDA_topic=tag_poem(content),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(poem)
        imported += 1
    
    db.session.commit()
    print(f"  [Success] Imported {imported} Caocao poems")
    return imported

def import_yuanqu(limit=328):
    """导入元曲（限制数量）"""
    filepath = os.path.join(DATA_DIR, '元曲', 'yuanqu.json')
    print(f"\n[Info] Importing Yuanqu: {filepath} (Limit {limit})")
    
    data = load_json_file(filepath)
    imported = 0
    
    for item in data[:limit]:
        # 提取曲牌名作为标题
        title = item.get('title', '无题')
        if '・' in title:
            title_parts = title.split('・')
            title = title_parts[1] if len(title_parts) > 1 else title
        
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
            genre_type='曲',
            rhythm_name=title,
            rhythm_type='元曲',
            LDA_topic=tag_poem(content),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(poem)
        imported += 1
    
    db.session.commit()
    print(f"  [Success] Imported {imported} Yuanqu poems")
    return imported

def main():
    """主函数"""
    print("=" * 60)
    print("批量导入诗歌数据 (重构版)")
    print("=" * 60)
    
    with app.app_context():
        # 初始化数据库表
        db.create_all()
        print("[DB] Database schema synchronized.")
        
        # 如果没有 LDA 模型，先尝试训练一个
        global LDA_MODEL, LDA_DICT, TOPIC_KW
        if LDA_MODEL is None:
            print("[Warning] No LDA model found, training from dataset.csv...")
            from lda_analysis import train_lda_on_poems, save_lda_model, load_data
            df = load_data()
            if not df.empty:
                # 使用 'comment' 字段作为训练文本 (dataset.csv 中是评论)
                text_data = df['comment'].tolist() if 'comment' in df.columns else df.iloc[:, 0].tolist()
                LDA_MODEL, LDA_DICT, TOPIC_KW = train_lda_on_poems(text_data)
                if LDA_MODEL:
                    save_lda_model(LDA_MODEL, LDA_DICT, TOPIC_KW)
        
        current_count = Poem.query.count()
        print(f"\n[Stats] Current poems count: {current_count}")
        
        import_caocao()
        import_song_ci()
        import_yuanqu(limit=328)
        
        new_count = Poem.query.count()
        print(f"\n[Stats] Final poems count: {new_count}")
        print(f"[Stats] New poems added: {new_count - current_count}")

if __name__ == '__main__':
    main()
