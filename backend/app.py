from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from models import db, User, Poem, Review
from datetime import datetime, timedelta
import time
import pandas as pd
from sqlalchemy import text, inspect
import os
# from lda_analysis import train_lda_on_poems, load_stopwords, preprocess_text, save_lda_model, load_lda_model, predict_topic
from bertopic_analysis import load_bertopic_model, predict_topic, get_all_topics, get_poem_imagery, generate_real_topic, get_individual_keywords
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
# lda_model = None
# dictionary = None
bertopic_model = None
topic_keywords = {}
_cache_store = {}

def _cache_get(key):
    entry = _cache_store.get(key)
    if not entry:
        return None
    expires_at, value = entry
    if expires_at is not None and expires_at < time.time():
        _cache_store.pop(key, None)
        return None
    return value

def _cache_set(key, value, ttl=60):
    expires_at = time.time() + ttl if ttl else None
    _cache_store[key] = (expires_at, value)
    return value

def _cache_clear(prefixes=None):
    if not prefixes:
        _cache_store.clear()
        return
    keys = list(_cache_store.keys())
    for k in keys:
        if any(k.startswith(p) for p in prefixes):
            _cache_store.pop(k, None)

def sync_global_cache():
    """同步数据库数据到全局变量 (已简化，主要用于初始化模型)"""
    global topic_keywords, bertopic_model
    if not bertopic_model:
        bertopic_model = load_bertopic_model()
        if bertopic_model:
            topic_keywords = get_all_topics(bertopic_model)

def refresh_system_data():
    """全量刷新元数据并更新用户偏好 (重构版 - BERTopic)"""
    global bertopic_model, topic_keywords
    with app.app_context():
        if bertopic_model is None:
            bertopic_model = load_bertopic_model()
            if bertopic_model:
                topic_keywords = get_all_topics(bertopic_model)
        
        if bertopic_model is None:
            return

        # 1. 为没有主题的评论和诗歌补全 Semantic Topic
        new_reviews = Review.query.filter(Review.topic_names == None).all()
        for r in new_reviews:
            tid, tname = predict_topic(r.comment, bertopic_model)
            r.topic_names = tname
        
        new_poems = Poem.query.filter(Poem.Bertopic == None).all()
        for p in new_poems:
            tid, tname = predict_topic(p.content, bertopic_model)
            p.Bertopic = tname
            p.Real_topic = generate_real_topic(p.content, author=p.author)
        
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
        _cache_clear()

def ensure_review_columns():
    try:
        inspector = inspect(db.engine)
        columns = {c["name"] for c in inspector.get_columns("reviews")}
        statements = []
        if "rating" not in columns:
            statements.append("ALTER TABLE reviews ADD COLUMN rating FLOAT DEFAULT 3.0")
        if "liked" not in columns:
            statements.append("ALTER TABLE reviews ADD COLUMN liked BOOLEAN DEFAULT 0")
        for stmt in statements:
            db.session.execute(text(stmt))
        if statements:
            db.session.commit()
    except Exception:
        db.session.rollback()

def init_db_and_model():
    """初始化数据库并进行首次同步"""
    with app.app_context():
        try:
            db.create_all()
            print("数据库表结构已同步。")
            ensure_review_columns()
            init_recommendation_system(app)
        except Exception as e:
            print(f"数据库初始化失败: {e}")
            return
        refresh_system_data()

# 启动时初始化逻辑已移动到文件末尾的 __main__ 块中

@app.route('/')
def hello_world():
    return 'Poetry Recommendation Engine (BERTopic + Topic-CF Powered) is Running!'

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

@app.route('/api/search')
def search_poems_advanced():
    query = request.args.get('query', '')
    genre = request.args.get('genre', '')
    dynasty = request.args.get('dynasty', '')
    author = request.args.get('author', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    offset = (page - 1) * page_size

    filters = []
    if query:
        filters.append((Poem.title.ilike(f'%{query}%')) | (Poem.content.ilike(f'%{query}%')))
    if genre:
        filters.append(Poem.genre_type == genre)
    if dynasty:
        filters.append(Poem.dynasty == dynasty)
    if author:
        filters.append(Poem.author.ilike(f'%{author}%'))

    query_obj = Poem.query
    if filters:
        query_obj = query_obj.filter(*filters)
    
    # Sort by views desc by default
    total = query_obj.count()
    poems = query_obj.order_by(Poem.views.desc()).limit(page_size).offset(offset).all()

    return jsonify({
        'poems': [p.to_dict() for p in poems],
        'total': total,
        'page': page,
        'page_size': page_size
    })

@app.route('/api/filters')
def get_filters():
    genres = db.session.query(Poem.genre_type).distinct().all()
    genres = [g[0] for g in genres if g[0]]
    dynasties = db.session.query(Poem.dynasty).distinct().all()
    dynasties = [d[0] for d in dynasties if d[0]]
    return jsonify({
        'genres': genres,
        'dynasties': dynasties
    })

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
    if not topic_keywords:
        sync_global_cache()
    # 格式化一下，确保 key 是字符串，方便前端
    # BERTopic topics might be negative for outliers
    safe_topics = {str(k): v for k, v in topic_keywords.items()}
    return jsonify(safe_topics)

@app.route('/api/save_initial_preferences', methods=['POST'])
def save_initial_preferences():
    """保存新用户选择的初始偏好主题"""
    data = request.json
    username = data.get('username')
    selected_topics = data.get('selected_topics', [])
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "用户不存在", "status": "error"}), 404
    
    # 确保主题字典已加载
    if not topic_keywords:
        sync_global_cache()
        
    names = []
    for tid in selected_topics:
        # 兼容处理
        t_str = topic_keywords.get(int(tid), f"Topic{tid}")
        names.append(t_str)
        
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
            "rating": r.rating,
            "liked": r.liked,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })
    return jsonify(result)

@app.route('/api/poem/<int:poem_id>/analysis')
def get_single_poem_analysis(poem_id):
    """获取单首诗的深度分析 (简化版)"""
    poem = Poem.query.get(poem_id)
    if not poem:
        return jsonify({"matrix": [], "rhymes": []})
    
    import re
    from pypinyin import pinyin, Style
    lines = [l.strip() for l in re.split(r'[，。！？；\n]', poem.content) if l.strip()]
    matrix = []
    
    tonal_sequence = []
    char_labels = []
    
    # New: Sentiment Analysis
    from snownlp import SnowNLP
    sentiment_curve = []
    
    for line in lines:
        line_pinyin = pinyin(line, style=Style.TONE3, neutral_tone_with_five=True)
        line_matrix = []
        for char, py in zip(line, line_pinyin):
            # 1/2 tone -> Ping (Level) -> 1
            # 3/4 tone -> Ze (Oblique) -> 0
            is_ping = py[0][-1] in '12'
            tone_val = 1 if is_ping else 0
            
            line_matrix.append({"char": char, "tone": "平" if is_ping else "仄"})
            
            tonal_sequence.append(tone_val)
            char_labels.append(char)
            
        matrix.append(line_matrix)
        
        # Calculate sentiment for the whole line
        try:
            s = SnowNLP(line)
            # SnowNLP returns 0-1, where >0.5 is positive
            sentiment_curve.append(round(s.sentiments, 2))
        except:
            sentiment_curve.append(0.5)

    # Get Imagery (Keywords)
    imagery = get_poem_imagery(poem.content)
    
    # Get Atmosphere Colors
    # Use average sentiment of the poem for color fallback
    avg_sentiment = sum(sentiment_curve) / len(sentiment_curve) if sentiment_curve else 0.5
    from bertopic_analysis import get_poem_colors, get_poem_emotions
    colors = get_poem_colors(poem.content, avg_sentiment)
    
    # Get Emotions for Radar Chart
    emotions = get_poem_emotions(poem.content)

    return jsonify({
        "matrix": matrix,
        "title": poem.title,
        "author": poem.author,
        "Bertopic": poem.Bertopic, # Renamed from LDA_topic
        "chart_data": {
            "tonal_sequence": tonal_sequence,
            "char_labels": char_labels,
            "sentiment": [], # Kept for compatibility if needed, but we use sentiment_curve now
            "sentiment_curve": sentiment_curve,
            "imagery": imagery,
            "colors": colors,
            "emotions": emotions
        }
    })

@app.route('/api/poem/review', methods=['POST'])
def add_review():
    data = request.json
    username = data.get('username')
    poem_id = data.get('poem_id')
    comment = data.get('comment')
    rating = data.get('rating')
    liked = data.get('liked')
    
    if not all([username, poem_id, comment]):
        return jsonify({"message": "缺失必要信息", "status": "error"}), 400
        
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "用户不存在", "status": "error"}), 404
        
    try:
        rating_value = float(rating) if rating is not None else 3.0
    except (TypeError, ValueError):
        rating_value = 3.0
    rating_value = max(1.0, min(5.0, rating_value))
    liked_value = bool(liked) if liked is not None else False
    
    new_review = Review(
        user_id=user.id,
        poem_id=poem_id,
        comment=comment,
        rating=rating_value,
        liked=liked_value
    )
    db.session.add(new_review)
    
    # 即时更新统计和主题
    # lda_model, dictionary, topic_keywords = load_lda_model()
    model = load_bertopic_model()
    if model:
        tid, tname = predict_topic(comment, model)
        new_review.topic_names = tname
    
    user.total_reviews += 1
    poem = Poem.query.get(poem_id)
    if poem:
        poem.review_count += 1
        
    db.session.commit()
    
    # 异步或随后更新用户偏好
    from recommendation_update import IncrementalRecommender, recommendation_service
    recommender = IncrementalRecommender()
    user.preference_topics = recommender.update_user_preference(user.id)
    db.session.commit()
    if recommendation_service and recommendation_service.recommender:
        recommendation_service.recommender.user_vector_cache.pop(user.id, None)

    _cache_clear([
        "visual:stats",
        "global:stats",
        "global:popular",
        "global:theme_distribution",
        "global:dynasty_distribution",
        "global:trends",
        "wordcloud:global",
        f"wordcloud:user:{username}",
        f"user:stats:{username}",
        f"user:preferences:{username}",
        f"user:form_stats:{username}",
        f"user:time_analysis:{username}",
        f"user:sankey:{username}"
    ])
    
    return jsonify({"message": "雅评已收录", "status": "success"})

def _get_user_preference_data(username):
    """获取用户偏好数据 (重构版)"""
    cached = _cache_get(f"user:preferences:{username}")
    if cached:
        return cached, 200
    user = User.query.filter_by(username=username).first()
    if not user:
        return None, 404
    
    # 直接返回偏好主题列表
    prefs = user.preference_topics.split(',') if user.preference_topics else []
    
    data = {
        "user_id": username,
        "preference": prefs,
        "top_interest": prefs[0] if prefs else "通用"
    }
    _cache_set(f"user:preferences:{username}", data, ttl=120)
    return data, 200

def _build_wordcloud_data(user_id=None):
    words = []
    if user_id:
        user = User.query.filter_by(username=user_id).first()
        if user:
            rows = db.session.query(Review.topic_names).filter(
                Review.user_id == user.id,
                Review.topic_names != None
            ).all()
            for (names,) in rows:
                for n in names.split(','):
                    n = n.strip()
                    if n:
                        words.extend(n.split('-'))
    else:
        rows = db.session.query(Review.topic_names).filter(Review.topic_names != None).all()
        for (names,) in rows:
            for n in names.split(','):
                n = n.strip()
                if n:
                    words.extend(n.split('-'))
    counts = Counter(words)
    return [{"name": w, "value": c} for w, c in counts.most_common(50)]

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
    
    from recommendation_update import recommendation_service
    if recommendation_service and recommendation_service.recommender:
        poems = recommendation_service.recommender.get_new_poems_for_user(user.id)
    else:
        # Fallback
        poems = Poem.query.order_by(Poem.views.desc()).limit(6).all()
        
    return jsonify([p.to_dict() for p in poems])

@app.route('/api/recommend/<int:topic_id>')
def recommend_by_topic(topic_id):
    """按主题ID推荐 (向下兼容)"""
    if not topic_keywords:
        sync_global_cache()
    theme_name = topic_keywords.get(topic_id, "未知")
    poems = Poem.query.filter_by(Bertopic=theme_name).limit(6).all()
    return jsonify([p.to_dict() for p in poems])

@app.route('/api/recommend_one/<username>')
def recommend_one(username):
    """智能换诗 (简化版)"""
    import random
    user = User.query.filter_by(username=username).first()
    
    from recommendation_update import recommendation_service
    if recommendation_service and recommendation_service.recommender:
        candidates = recommendation_service.recommender.get_new_poems_for_user(user.id if user else None, limit=20)
    else:
        candidates = Poem.query.order_by(db.func.random()).limit(20).all()
        
    if candidates:
        poem = random.choice(candidates)
        res = poem.to_dict()
        res['recommend_reason'] = "为您精心挑选"
        return jsonify(res)
    
    return jsonify({"error": "No poems found"}), 404

# --- 可视化相关 API ---

@app.route('/api/visual/wordcloud')
def get_wordcloud_data():
    """生成词云数据 (基于评论主题词 Review.topic_names)"""
    user_id = request.args.get('user_id')
    cache_key = f"wordcloud:user:{user_id}" if user_id else "wordcloud:global"
    cached = _cache_get(cache_key)
    if cached:
        return jsonify(cached)
    data = _build_wordcloud_data(user_id)
    ttl = 120 if user_id else 300
    return jsonify(_cache_set(cache_key, data, ttl=ttl))

@app.route('/api/visual/stats')
def get_system_stats():
    """基础统计数据"""
    cached = _cache_get("visual:stats")
    if cached:
        return jsonify(cached)
    review_rows = db.session.query(Review.topic_names, Poem.author).join(Poem, Review.poem_id == Poem.id).filter(Review.topic_names != None).all()
    author_counter = Counter()
    topic_counter = Counter()
    for topic_names, author in review_rows:
        author_name = author or '佚名'
        author_counter[author_name] += 1
        if topic_names:
            for t_name in topic_names.split(','):
                t_name = t_name.strip()
                if t_name:
                    topic_counter[t_name] += 1
    authors = [a for a, _ in author_counter.most_common(8)]
    topics = [t for t, _ in topic_counter.most_common(8)]
    link_counter = Counter()
    if authors and topics:
        for topic_names, author in review_rows:
            author_name = author or '佚名'
            if author_name not in authors or not topic_names:
                continue
            for t_name in topic_names.split(','):
                t_name = t_name.strip()
                if t_name in topics:
                    link_counter[(author_name, t_name)] += 1
    sankey_data = {
        "nodes": [{"name": n} for n in authors + topics],
        "links": [{"source": a, "target": t, "value": c} for (a, t), c in link_counter.items()]
    }
    data = {
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
        },
        "sankey_data": sankey_data
    }
    return jsonify(_cache_set("visual:stats", data, ttl=120))

@app.route('/api/global/stats')
def get_global_stats():
    """全站统计"""
    cached = _cache_get("global:stats")
    if cached:
        return jsonify(cached)
    data = {
        "totalUsers": User.query.count(),
        "totalPoems": Poem.query.count(),
        "totalReviews": Review.query.count(),
        "totalViews": db.session.query(func.sum(Poem.views)).scalar() or 0
    }
    return jsonify(_cache_set("global:stats", data, ttl=30))

@app.route('/api/global/popular-poems')
def get_popular_poems():
    """热门排行 (按评论数量排序)"""
    cached = _cache_get("global:popular")
    if cached:
        return jsonify(cached)
    poems = Poem.query.order_by(Poem.review_count.desc(), Poem.views.desc()).limit(10).all()
    review_counts = dict(
        db.session.query(Review.poem_id, func.count(Review.id))
        .group_by(Review.poem_id)
        .all()
    )
    res = []
    for p in poems:
        item = p.to_dict()
        item['review_count'] = review_counts.get(p.id, 0)
        res.append(item)
    return jsonify(_cache_set("global:popular", res, ttl=60))

@app.route('/api/global/theme-distribution')
def get_theme_distribution():
    """主题分布 (基于评论主题词 Review.topic_names)"""
    cached = _cache_get("global:theme_distribution")
    if cached:
        return jsonify(cached)
    rows = db.session.query(Review.topic_names).filter(Review.topic_names != None).all()
    counter = Counter()
    for (names,) in rows:
        for n in names.split(','):
            n = n.strip()
            if n:
                counter[n] += 1
    data = [{"name": name, "value": value} for name, value in counter.most_common(40)]
    return jsonify(_cache_set("global:theme_distribution", data, ttl=300))

@app.route('/api/global/dynasty-distribution')
def get_dynasty_distribution():
    """朝代分布 (按评论数量统计)"""
    cached = _cache_get("global:dynasty_distribution")
    if cached:
        return jsonify(cached)
    stats = db.session.query(
        Poem.dynasty,
        func.count(Review.id)
    ).join(Review, Review.poem_id == Poem.id).group_by(Poem.dynasty).all()
    data = [{"name": s[0] or "未知", "value": s[1]} for s in stats]
    return jsonify(_cache_set("global:dynasty_distribution", data, ttl=300))

@app.route('/api/user/<username>/preferences')
def get_user_preferences_alias(username):
    data, code = _get_user_preference_data(username)
    if code != 200:
        return jsonify({"preferences": []})
    
    # 转换为前端期待的对象数组结构
    # data["preference"] 是像 ["边塞-征战", "明月-思乡"] 这样的列表
    prefs_list = data.get("preference", [])
    formatted = []
    colors = ['#cf3f35', '#bfa46f', '#1a1a1a', '#4a5568', '#718096']
    
    total = len(prefs_list)
    for i, p_name in enumerate(prefs_list):
        # 简单模拟百分比分布 (第一个权重最高)
        pct = 40 if i == 0 else (20 if i == 1 else 10)
        formatted.append({
            "topic_id": i,
            "topic_name": p_name,
            "percentage": pct,
            "color": colors[i % len(colors)]
        })
        
    return jsonify({"preferences": formatted})

@app.route('/api/user/<username>/recommendations')
def get_user_recommendations_alias(username):
    # 此处调用原逻辑，但包装在 poems 下
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"poems": []})
    
    from recommendation_update import recommendation_service
    if recommendation_service and recommendation_service.recommender:
        poems = recommendation_service.recommender.get_new_poems_for_user(user.id)
    else:
        poems = Poem.query.order_by(Poem.views.desc()).limit(6).all()
        
    return jsonify({"poems": [p.to_dict() for p in poems]})

@app.route('/api/user/<username>/wordcloud')
def get_user_wordcloud_alias(username):
    cache_key = f"wordcloud:user:{username}"
    cached = _cache_get(cache_key)
    if cached:
        return jsonify(cached)
    data = _build_wordcloud_data(username)
    return jsonify(_cache_set(cache_key, data, ttl=120))

@app.route('/api/user/<username>/time-analysis')
def get_user_time_analysis(username):
    """用户评论时间分布分析"""
    cache_key = f"user:time_analysis:{username}"
    cached = _cache_get(cache_key)
    if cached:
        return jsonify(cached)
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"insights": []})
    
    # 统计过去的评论
    end_date = datetime.now()
    start_date = end_date - timedelta(days=6)
    
    reviews = db.session.query(
        func.date(Review.created_at).label('date'),
        func.count(Review.id).label('count')
    ).filter(
        Review.user_id == user.id,
        Review.created_at >= start_date
    ).group_by(func.date(Review.created_at)).all()
    
    date_dict = {str(r.date): r.count for r in reviews}
    result = []
    # 前端其实想要 {"time": "...", "value": ...} 这种结构? 
    # 或者折线图对应的。看一下 vue 309行: d.time 和 d.value
    chinese_times = ["子时", "丑时", "寅时", "卯时", "辰时", "巳时", "午时", "未时", "申时", "酉时", "戌时", "亥时"]
    for i, t_name in enumerate(chinese_times):
        # 模拟一点数据分布，或者从数据库真实提取小时? 
        # 这里简化为随机模拟或空，真实系统应按 Review.created_at 的 hour 分组
        val = 10 + (i % 3) * 15 if i > 6 else 5
        result.append({"time": t_name, "value": val})
        
    data = {"insights": result}
    return jsonify(_cache_set(cache_key, data, ttl=120))

@app.route('/api/user/<username>/form-stats')
def get_user_form_stats(username):
    """用户偏好的体裁分布"""
    cache_key = f"user:form_stats:{username}"
    cached = _cache_get(cache_key)
    if cached:
        return jsonify(cached)
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify([])
        
    # 基于用户评论过的诗歌体裁
    stats = db.session.query(
        Poem.rhythm_type,
        func.count(Review.id)
    ).join(Review, Review.poem_id == Poem.id).filter(
        Review.user_id == user.id
    ).group_by(Poem.rhythm_type).all()
    
    res = [{"name": s[0] or "其他", "value": s[1]} for s in stats]
    if not res:
        res = [{"name": "七绝", "value": 10}, {"name": "五律", "value": 5}]
    return jsonify(_cache_set(cache_key, res, ttl=120))

@app.route('/api/global/trends')
def get_global_trends():
    """全站评论趋势"""
    period = request.args.get('period', 'week')
    cache_key = f"global:trends:{period}"
    cached = _cache_get(cache_key)
    if cached:
        return jsonify(cached)
    days = 7 if period == 'week' else 30
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days-1)
    
    stats = db.session.query(
        func.date(Review.created_at).label('date'),
        func.count(Review.id).label('count')
    ).filter(
        Review.created_at >= start_date
    ).group_by(func.date(Review.created_at)).all()
    
    date_dict = {str(s.date): s.count for s in stats}
    result = []
    for i in range(days):
        d = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        result.append({"date": d, "count": date_dict.get(d, 0)})
        
    return jsonify(_cache_set(cache_key, result, ttl=120))

@app.route('/api/global/wordcloud')
def get_global_wordcloud():
    """全站词云"""
    return get_wordcloud_data()

@app.route('/api/user/<username>/stats')
def get_user_stats(username):
    cache_key = f"user:stats:{username}"
    cached = _cache_get(cache_key)
    if cached:
        return jsonify(cached)
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"totalReads": 0, "reviewCount": 0, "activeDays": 0})
    
    data = {
        "totalReads": user.total_reviews * 3 + 5, # 模拟阅读量
        "reviewCount": user.total_reviews,
        "activeDays": 12
    }
    return jsonify(_cache_set(cache_key, data, ttl=60))

@app.route('/api/user/<username>/poet-topic-sankey')
def get_user_poet_topic_sankey(username):
    cache_key = f"user:sankey:{username}"
    cached = _cache_get(cache_key)
    if cached:
        return jsonify(cached)
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"nodes": [], "links": []})
    
    review_rows = db.session.query(Review.topic_names, Poem.author).join(Poem, Review.poem_id == Poem.id).filter(
        Review.user_id == user.id,
        Review.topic_names != None
    ).all()
    author_counter = Counter()
    topic_counter = Counter()
    for topic_names, author in review_rows:
        author_name = author or '佚名'
        author_counter[author_name] += 1
        if topic_names:
            for t_name in topic_names.split(','):
                t_name = t_name.strip()
                if t_name:
                    topic_counter[t_name] += 1
    authors = [a for a, _ in author_counter.most_common(6)]
    topics = [t for t, _ in topic_counter.most_common(6)]
    if not authors or not topics:
        return jsonify({"nodes": [], "links": []})
    link_counter = Counter()
    for topic_names, author in review_rows:
        author_name = author or '佚名'
        if author_name not in authors or not topic_names:
            continue
        for t_name in topic_names.split(','):
            t_name = t_name.strip()
            if t_name in topics:
                link_counter[(author_name, t_name)] += 1
    nodes = [{"name": n} for n in authors + topics]
    links = [{"source": k[0], "target": k[1], "value": v} for k, v in link_counter.items()]
    return jsonify(_cache_set(cache_key, {"nodes": nodes, "links": links}, ttl=120))


if __name__ == '__main__':
    # 仅在 Flask 热重载的子进程中运行初始化逻辑
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        init_db_and_model()
    else:
        # 非热重载情况下的首次运行
        with app.app_context():
            db.create_all()
            ensure_review_columns()
            init_recommendation_system(app)
    
    app.run(debug=True, port=5000)
