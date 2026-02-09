import os
import json
import random
import shutil
import argparse
from app import app
from models import db, Poem
import bertopic_analysis

# 配置路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POETRY_DATA_DIR = os.path.join(BASE_DIR, 'data', 'chinese-poetry')

def collect_poetry_data(sample_limit=20000):
    all_content = []
    # 增加扫描范围
    targets = [
        ('全唐诗', 300), 
        ('宋词', 30),
        ('元曲', 10),
        ('曹操诗集', None),
        ('诗经', None),
        ('楚辞', None),
        ('御定全唐詩', 300)
    ]
    
    print("[BERTopic] Collecting poetry samples...")
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
                                # 过滤极短文本，但保留绝句律诗长度
                                if len(content) > 10:
                                    all_content.append(content)
            except: pass
                
    total = len(all_content)
    print(f"[BERTopic] Total poems found: {total}")
    
    if total > sample_limit:
        print(f"[BERTopic] Sampling {sample_limit} poems for training...")
        return random.sample(all_content, sample_limit)
    return all_content

def fill_real_topics(limit=0, batch_size=200, dry_run=False):
    with app.app_context():
        query = Poem.query.order_by(Poem.id.asc())
        if limit and limit > 0:
            query = query.limit(int(limit))
        poems = query.all()
        total = len(poems)
        print(f"[RealTopic] Updating Real_topic for {total} poems...")

        updated = 0
        for i, p in enumerate(poems):
            # 使用新逻辑生成模拟评论标签
            p.Real_topic = bertopic_analysis.generate_real_topic(p.content, author=p.author)
            updated += 1

            if batch_size and (i + 1) % int(batch_size) == 0:
                if not dry_run:
                    db.session.commit()
                print(f"  - Progress: {i+1}/{total}")

        if not dry_run:
            db.session.commit()
        print(f"[Success] Updated Real_topic for {updated} poems.")

def train_and_update_topics():
    # 1. 准备数据
    docs = collect_poetry_data(sample_limit=20000)
    
    # 2. 训练模型
    # train_bertopic_model 内部会加载 embedding model 并调用 fit_transform
    print("[BERTopic] Starting training... (This may take a while)")
    model, topics, probs = bertopic_analysis.train_bertopic_model(docs)
    
    # 3. 保存模型
    bertopic_analysis.save_bertopic_model(model)
    
    # 4. 更新数据库
    print("[BERTopic] Updating database with new semantic topics...")
    with app.app_context():
        poems = Poem.query.all()
        total_poems = len(poems)
        
        # 批量处理以提高效率，虽然这里是简单的循环
        for i, p in enumerate(poems):
            # predict_topic 需要载入模型，但这里我们已经有 model 对象了
            # 为了复用 bertopic_analysis.predict_topic 逻辑，我们可以传递 model
            # 或者直接调用 model.transform 因为 predict_topic 内部也是 transform
            
            # transform 较慢，如果是大量数据最好批量 transform
            # 但这里数据库目前只有 ~800 条，单条预测尚可
            
            topic_id, topic_name = bertopic_analysis.predict_topic(p.content, model)
            p.Bertopic = topic_name
            p.Real_topic = bertopic_analysis.generate_real_topic(p.content, author=p.author)
            
            if (i+1) % 50 == 0:
                print(f"  - Progress: {i+1}/{total_poems}")
                db.session.commit() # 阶段性提交
        
        db.session.commit()
        print(f"[Success] Updated {total_poems} poems with BERTopic tags.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["train", "fill-real-topic"], default="train")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.mode == "fill-real-topic":
        fill_real_topics(limit=args.limit, batch_size=args.batch_size, dry_run=args.dry_run)
    else:
        train_and_update_topics()
