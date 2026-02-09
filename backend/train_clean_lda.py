import os
import json
import random
from gensim import corpora, models
from app import app
from models import db, Poem
import lda_analysis
import shutil

# 配置路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POETRY_DATA_DIR = os.path.join(BASE_DIR, 'data', 'chinese-poetry')

def collect_poetry_data(sample_limit=15000):
    all_content = []
    targets = [
        ('全唐诗', 200), 
        ('宋词', None),
        ('元曲', None),
        ('曹操诗集', None),
        ('诗经', None),
        ('楚辞', None),
        ('御定全唐詩', 200)
    ]
    
    print("[Clean-LDA] Collecting high-quality poetry samples...")
    
    for folder, file_limit in targets:
        dir_path = os.path.join(POETRY_DATA_DIR, folder)
        if not os.path.exists(dir_path): continue
            
        files = [f for f in os.listdir(dir_path) if f.endswith('.json')]
        if file_limit: files = files[:file_limit]
            
        for filename in files:
            file_path = os.path.join(dir_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            paragraphs = item.get('paragraphs', [])
                            if paragraphs:
                                content = "".join(paragraphs)
                                if len(content) > 15: # 提高短诗过滤阈值
                                    all_content.append(content)
            except: pass
                
    if len(all_content) > sample_limit:
        return random.sample(all_content, sample_limit)
    return all_content

def main():
    # 彻底清理旧模型
    if os.path.exists('saved_models'):
        shutil.rmtree('saved_models')
        print("[Clean-LDA] Purged old models.")

    # 1. 采集大规模样本
    raw_texts = collect_poetry_data(sample_limit=15000)
    
    # 2. 训练（lda_analysis.py 内部已集成 POS 过滤和 TF-IDF）
    print(f"[Clean-LDA] Starting optimized training with K=60...")
    lda, dictionary, topic_keywords = lda_analysis.train_lda_on_poems(raw_texts, num_topics=60)
    
    if lda:
        # 3. 保存
        lda_analysis.save_lda_model(lda, dictionary, topic_keywords)
        print("[Clean-LDA] Optimized model stored.")
        
        # 4. 刷新数据库每首诗的主题概率
        print("[Clean-LDA] Synchronizing DB entries with new high-purity topics...")
        with app.app_context():
            poems = Poem.query.all()
            for i, p in enumerate(poems):
                p.Bertopic = lda_analysis.predict_topic(p.content, lda, dictionary, topic_keywords)
                if i % 100 == 0:
                    print(f"  - DB Sync: {i}/{len(poems)}")
            db.session.commit()
            print(f"[Success] System upgraded with Clean-LDA (K=60).")

if __name__ == '__main__':
    main()
