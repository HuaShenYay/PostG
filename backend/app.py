from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from models import db, User, Poem, Review
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import text
import os
from lda_analysis import train_lda_on_poems, load_stopwords, preprocess_text, save_lda_model, load_lda_model, predict_topic
import json
from collections import Counter
from sqlalchemy import func
from recommendation_update import add_recommendation_routes, init_recommendation_system

app = Flask(__name__)
app.config.from_object(Config)

# 初始化插件
CORS(app)
db.init_app(app)

# 初始化推荐更新系统
add_recommendation_routes(app)

# --- 全局变量 ---
lda_model = None
dictionary = None
df_data = None
topic_keywords = {}

def sync_global_cache():
    """同步数据库数据到全局变量 (已简化，主要用于初始化模型)"""
    global topic_keywords, lda_model, dictionary
    if not topic_keywords:
        lda_model, dictionary, topic_keywords = load_lda_model()

def refresh_system_data():
    """全量刷新元数据并更新用户偏好 (重构版)"""
    global lda_model, dictionary, topic_keywords
    with app.app_context():
        if lda_model is None:
            lda_model, dictionary, topic_keywords = load_lda_model()
        if lda_model is None:
            return

        # 1. 为没有主题的评论和诗歌补全 LDA 主题
        new_reviews = Review.query.filter(Review.topic_names == None).all()
        for r in new_reviews:
            r.topic_names = predict_topic(r.comment, lda_model, dictionary, topic_keywords)
        
        new_poems = Poem.query.filter(Poem.LDA_topic == None).all()
        for p in new_poems:
            p.LDA_topic = predict_topic(p.content, lda_model, dictionary, topic_keywords)
        
        db.session.commit()

        # 2. 更新所有用户的偏好和评论计数
        from recommendation_update import IncrementalRecommender
        recommender = IncrementalRecommender()
        users = User.query.all()
        for u in users:
            u.preference_topics = recommender.update_user_preference(u.id)
            u.total_reviews = Review.query.filter_by(user_id=u.id).count()
        
        # 3. 更新诗歌的评论计数
        poems = Poem.query.all()
        for p in poems:
            p.review_count = Review.query.filter_by(poem_id=p.id).count()
            
        db.session.commit()

def init_db_and_model():
    """初始化数据库并进行首次同步"""
    with app.app_context():
        try:
            db.create_all()
            print("数据库表结构已同步。")
            init_recommendation_system(app)
        except Exception as e:
            print(f"数据库初始化失败: {e}")
            return
        refresh_system_data()

# 启动时初始化逻辑已移动到文件末尾的 __main__ 块中

@app.route('/')
def hello_world():
    return 'Poetry Recommendation Engine (LDA Powered) is Running!'

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"message": "请输入账号和密码", "status": "error"}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        return jsonify({
            "message": "登录成功",
            "status": "success",
            "user": user.to_dict()
        })
    else:
        return jsonify({"message": "账号或口令有误", "status": "error"}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"message": "请输入账号和密码", "status": "error"}), 400
    
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"message": "此称谓已被占用", "status": "error"}), 400
    
    try:
        new_user = User(username=username, password_hash=password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "注册成功，即将开启诗意之旅", "status": "success"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"注册失败: {str(e)}", "status": "error"}), 500

@app.route('/api/user/update', methods=['POST'])
def update_user():
    data = request.json
    old_username = data.get('old_username')
    new_username = data.get('new_username')
    new_password = data.get('new_password')
    
    if not old_username:
        return jsonify({"message": "无效的操作", "status": "error"}), 400
        
    user = User.query.filter_by(username=old_username).first()
    if not user:
        return jsonify({"message": "用户不存在", "status": "error"}), 404
        
    if new_username and new_username != old_username:
        existing = User.query.filter_by(username=new_username).first()
        if existing:
            return jsonify({"message": "新称谓已被占用", "status": "error"}), 400
        user.username = new_username
        
    if new_password:
        user.password_hash = new_password
        
    try:
        db.session.commit()
        return jsonify({
            "message": "修缮成功", 
            "status": "success",
            "user": user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"修缮失败: {str(e)}", "status": "error"}), 500

@app.route('/api/poems')
def get_poems():
    poems = Poem.query.limit(20).all()
    return jsonify([p.to_dict() for p in poems])

@app.route('/api/poem/<int:poem_id>')
def get_poem(poem_id):
    poem = Poem.query.get(poem_id)
    if not poem:
        return jsonify({"error": "Poem not found"}), 404
    return jsonify(poem.to_dict())

@app.route('/api/search_poems')
def search_poems():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    results = Poem.query.filter(
        (Poem.title.ilike(f'%{query}%')) |
        (Poem.author.ilike(f'%{query}%')) |
        (Poem.content.ilike(f'%{query}%'))
    ).limit(20).all()
    
    return jsonify([p.to_dict() for p in results])

@app.route('/api/topics')
def get_topics():
    return jsonify(topic_keywords)

@app.route('/api/save_initial_preferences', methods=['POST'])
def save_initial_preferences():
    """保存新用户选择的初始偏好主题"""
    data = request.json
    username = data.get('username')
    selected_topics = data.get('selected_topics', [])
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "用户不存在", "status": "error"}), 404
    
    # 转换为主题名存储
    names = [topic_keywords.get(int(tid), f"主题-{tid}") for tid in selected_topics]
    user.preference_topics = ",".join(names)
    db.session.commit()
    
    return jsonify({"message": "偏好设置成功", "status": "success"})

@app.route('/api/poem/<int:poem_id>/reviews')
def get_poem_reviews(poem_id):
    reviews = Review.query.filter_by(poem_id=poem_id).all()
    result = []
    for r in reviews:
        user = User.query.get(r.user_id)
        result.append({
            "id": r.id,
            "username": user.username if user else "匿名",
            "comment": r.comment,
            "topic_names": r.topic_names,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })
    return jsonify(result)

@app.route('/api/poem/<int:poem_id>/analysis')
def get_single_poem_analysis(poem_id):
    """获取单首诗的深度分析 (简化版)"""
    poem = Poem.query.get(poem_id)
    if not poem:
        return jsonify({"matrix": [], "rhymes": []})
    
    # 这里可以保留原来的音律分析逻辑，或者简化
    # 为了保持功能的“酷炫”，我们尽量保留逻辑
    import re
    from pypinyin import pinyin, Style
    lines = [l.strip() for l in re.split(r'[，。！？；\n]', poem.content) if l.strip()]
    matrix = []
    for line in lines:
        line_pinyin = pinyin(line, style=Style.TONE3, neutral_tone_with_five=True)
        line_matrix = [{"char": char, "tone": "平" if (py[0][-1] in '12') else "仄"} for char, py in zip(line, line_pinyin)]
        matrix.append(line_matrix)
    
    return jsonify({
        "matrix": matrix,
        "title": poem.title,
        "author": poem.author,
        "LDA_topic": poem.LDA_topic
    })

@app.route('/api/poem/review', methods=['POST'])
def add_review():
    data = request.json
    username = data.get('username')
    poem_id = data.get('poem_id')
    comment = data.get('comment')
    
    if not all([username, poem_id, comment]):
        return jsonify({"message": "缺失必要信息", "status": "error"}), 400
        
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "用户不存在", "status": "error"}), 404
        
    new_review = Review(
        user_id=user.id,
        poem_id=poem_id,
        comment=comment
    )
    db.session.add(new_review)
    
    # 即时更新统计和主题
    lda_model, dictionary, topic_keywords = load_lda_model()
    if lda_model:
        new_review.topic_names = predict_topic(comment, lda_model, dictionary, topic_keywords)
    
    user.total_reviews += 1
    poem = Poem.query.get(poem_id)
    if poem:
        poem.review_count += 1
        
    db.session.commit()
    
    # 异步或随后更新用户偏好
    from recommendation_update import IncrementalRecommender
    recommender = IncrementalRecommender()
    user.preference_topics = recommender.update_user_preference(user.id)
    db.session.commit()
    
    return jsonify({"message": "雅评已收录", "status": "success"})

def _get_user_preference_data(username):
    """获取用户偏好数据 (重构版)"""
    user = User.query.filter_by(username=username).first()
    if not user:
        return None, 404
    
    # 直接返回偏好主题列表
    prefs = user.preference_topics.split(',') if user.preference_topics else []
    
    return {
        "user_id": username,
        "preference": prefs,
        "top_interest": prefs[0] if prefs else "通用"
    }, 200

@app.route('/api/user_preference/<username>')
def get_user_preference(username):
    data, code = _get_user_preference_data(username)
    if code != 200:
        return jsonify({"user_id": username, "preference": [], "top_interest": "通用"})
    return jsonify(data)

@app.route('/api/recommend_personal/<username>')
def recommend_personal(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify([])
    
    from recommendation_update import IncrementalRecommender
    recommender = IncrementalRecommender()
    poems = recommender.get_new_poems_for_user(user.id)
    return jsonify([p.to_dict() for p in poems])

@app.route('/api/recommend/<int:topic_id>')
def recommend_by_topic(topic_id):
    """按主题ID推荐 (向下兼容)"""
    theme_name = topic_keywords.get(topic_id, "未知")
    poems = Poem.query.filter_by(LDA_topic=theme_name).limit(6).all()
    return jsonify([p.to_dict() for p in poems])

@app.route('/api/recommend_one/<username>')
def recommend_one(username):
    """智能换诗 (简化版)"""
    import random
    user = User.query.filter_by(username=username).first()
    
    from recommendation_update import IncrementalRecommender
    recommender = IncrementalRecommender()
    
    # 获取一批推荐
    candidates = recommender.get_new_poems_for_user(user.id if user else None, limit=20)
    if candidates:
        poem = random.choice(candidates)
        res = poem.to_dict()
        res['recommend_reason'] = "为您精心挑选"
        return jsonify(res)
    
    # 兜底：随机一首
    poem = Poem.query.order_by(db.func.random()).first()
    if poem:
        return jsonify(poem.to_dict())
    return jsonify({"error": "No poems found"}), 404

# --- 可视化相关 API ---

@app.route('/api/visual/wordcloud')
def get_wordcloud_data():
    """生成词云数据 (基于主题名)"""
    user_id = request.args.get('user_id')
    processed_words = []
    
    if user_id:
        user = User.query.filter_by(username=user_id).first()
        if user and user.preference_topics:
            topics = user.preference_topics.split(',')
            for topic in topics:
                processed_words.extend(topic.split('-'))
    
    if not processed_words:
        all_topics = db.session.query(Poem.LDA_topic).distinct().limit(50).all()
        for t in all_topics:
            if t[0]:
                processed_words.extend(t[0].split('-'))
                
    word_counts = Counter(processed_words)
    data = [{"name": w, "value": c} for w, c in word_counts.most_common(50)]
    return jsonify(data)

@app.route('/api/visual/stats')
def get_system_stats():
    """基础统计数据"""
    return jsonify({
        "counts": {
            "users": User.query.count(),
            "poems": Poem.query.count(),
            "reviews": Review.query.count()
        },
        "radar_data": {
            "indicator": [{"name": "诗", "max": 100}, {"name": "词", "max": 100}, {"name": "曲", "max": 100}],
            "value": [
                Poem.query.filter_by(genre_type='诗').count(),
                Poem.query.filter_by(genre_type='词').count(),
                Poem.query.filter_by(genre_type='曲').count()
            ]
        }
    })

@app.route('/api/global/stats')
def get_global_stats():
    """全站统计"""
    return jsonify({
        "totalUsers": User.query.count(),
        "totalPoems": Poem.query.count(),
        "totalReviews": Review.query.count(),
        "totalViews": db.session.query(func.sum(Poem.views)).scalar() or 0
    })

@app.route('/api/global/popular-poems')
def get_popular_poems():
    """热门排行 (基于浏览量)"""
    poems = Poem.query.order_by(Poem.views.desc()).limit(10).all()
    return jsonify([p.to_dict() for p in poems])

@app.route('/api/global/theme-distribution')
def get_theme_distribution():
    """主题分布"""
    stats = db.session.query(Poem.LDA_topic, func.count(Poem.id)).group_by(Poem.LDA_topic).all()
    return jsonify([{"name": s[0] or "未知", "value": s[1]} for s in stats])

@app.route('/api/global/dynasty-distribution')
def get_dynasty_distribution():
    """朝代分布"""
    stats = db.session.query(Poem.dynasty, func.count(Poem.id)).group_by(Poem.dynasty).all()
    return jsonify([{"name": s[0] or "未知", "value": s[1]} for s in stats])

@app.route('/api/user/profile/<username>')
def get_user_profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict())

@app.route('/api/user/<username>/stats')
def get_user_stats(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({})
    return jsonify({
        "reviewCount": user.total_reviews,
        "preference": user.preference_topics
    })

if __name__ == '__main__':
    # 仅在 Flask 热重载的子进程中运行初始化逻辑
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        init_db_and_model()
    else:
        # 非热重载情况下的首次运行
        with app.app_context():
            db.create_all()
            init_recommendation_system(app)
    
    app.run(debug=True, port=5000)
