from flask import Flask
from config import Config
from models import db, User, Poem, Review
import json
import pandas as pd
import os

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def reset_db():
    """重置数据库：清空所有表"""
    with app.app_context():
        # 删除所有表
        db.drop_all()
        # 重新创建表
        db.create_all()
        print("数据库已重置 (所有数据已清空)")

def import_tang_poems():
    """导入唐诗三百首"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, '../data/chinese-poetry/全唐诗/唐诗三百首.json')
    
    with app.app_context():
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"找到 {len(data)} 首唐诗，开始导入...")
        
        count = 0
        for item in data:
            # paragraphs 是一个列表，需要合并成字符串
            content = "\n".join(item.get('paragraphs', []))
            
            poem = Poem(
                title=item.get('title'),
                author=item.get('author'),
                content=content
            )
            db.session.add(poem)
            count += 1
            
        db.session.commit()
        print(f"成功导入 {count} 首唐诗到数据库！")

def import_reviews():
    """导入评论数据，并关联到数据库里的诗歌"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, '../data/dataset.csv')
    df = pd.read_csv(csv_path)
    
    with app.app_context():
        # 1. 导入用户
        unique_users = df['user_id'].unique()
        for username in unique_users:
            if not User.query.filter_by(username=username).first():
                user = User(username=username)
                db.session.add(user)
        db.session.commit()
        print(f"导入用户 {len(unique_users)} 个")
        
        # 2. 建立映射缓存
        # 用户名 -> ID
        user_map = {u.username: u.id for u in User.query.all()}
        # 诗歌标题 -> ID (注意：数据库里可能有同名诗，这里简单取第一个)
        # 为了模糊匹配，我们先查出所有诗歌
        all_poems = Poem.query.all()
        # 构造 title -> id 的字典
        # 注意：唐诗三百首有些标题可能包含 "鼓吹曲辭 " 这种前缀，我们需要小心处理
        # 这里先做一个简单匹配
        poem_map = {p.title: p.id for p in all_poems}
        
        # 3. 导入评论
        matched_count = 0
        unmatched_titles = set()
        
        for _, row in df.iterrows():
            csv_title = row['poem_title']
            
            # 尝试查找
            poem_id = poem_map.get(csv_title)
            
            # 如果没找到，尝试模糊匹配（例如 CSV 是 "出塞"，数据库是 "横吹曲辞 出塞"）
            if not poem_id:
                for db_title, db_id in poem_map.items():
                    if csv_title in db_title:
                        poem_id = db_id
                        break
            
            if poem_id:
                review = Review(
                    user_id=user_map[row['user_id']],
                    poem_id=poem_id,
                    rating=int(row['rating']),
                    comment=row['comment']
                )
                db.session.add(review)
                matched_count += 1
            else:
                unmatched_titles.add(csv_title)
                
        db.session.commit()
        print(f"导入评论 {matched_count} 条")
        if unmatched_titles:
            print(f"以下由于标题不匹配，未导入评论的诗歌 ({len(unmatched_titles)}首): {list(unmatched_titles)[:5]}...")

if __name__ == "__main__":
    reset_db()
    import_tang_poems()
    import_reviews()
