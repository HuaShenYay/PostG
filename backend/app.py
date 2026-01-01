from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from models import db, User, Poem, Review
import pandas as pd
from sqlalchemy import text
import os
from lda_analysis import train_lda_model, load_stopwords, preprocess_text

app = Flask(__name__)
app.config.from_object(Config)

# 初始化插件
CORS(app)
db.init_app(app)

# --- 全局变量 ---
lda_model = None
dictionary = None
df_data = None
topic_keywords = {}
doc_topic_probs = {} # 缓存每条评论的主题分布

def refresh_system_data():
    """实时刷新系统推荐模型 (使用 LDA)"""
    global lda_model, dictionary, df_data, topic_keywords, doc_topic_probs
    
    with app.app_context():
        print("正在同步数据库数据并刷新 LDA 模型...")
        sql = text("""
            SELECT 
                u.username as user_id, 
                p.title as poem_title, 
                r.rating, 
                r.comment 
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            JOIN poems p ON r.poem_id = p.id
        """)
        
        try:
             df_db = pd.read_sql(sql, db.session.connection())
        except Exception:
             df_db = pd.read_sql(sql, db.engine)

        if len(df_db) == 0:
            print("数据不足，无法训练模型。")
            return

        # 调用 LDA 训练逻辑 (返回 lda, dict, df, keywords)
        lda, gensim_dict, df, keywords = train_lda_model(df_db)
        
        # 更新全局缓存
        lda_model = lda
        dictionary = gensim_dict
        df_data = df
        topic_keywords = keywords
        
        # 预计算所有文档的主题分布
        stopwords = load_stopwords()
        doc_topic_probs = {}
        for idx, row in df.iterrows():
            tokens = preprocess_text(str(row['comment']), stopwords)
            bow = dictionary.doc2bow(tokens)
            # lda[bow] 返回 [(topic_id, prob), ...]
            doc_topic_probs[idx] = dict(lda_model[bow])
            
        print("LDA 模型及其索引已同步更新。")

def init_db_and_model():
    """初始化数据库并进行首次训练"""
    with app.app_context():
        try:
            db.create_all()
            print("数据库连接正常。")
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return
        
        refresh_system_data()

# 启动时初始化
init_db_and_model()

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
            "message": "入梦成功",
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

@app.route('/api/poems')
def get_poems():
    poems = Poem.query.limit(20).all()
    return jsonify([p.to_dict() for p in poems])

@app.route('/api/topics')
def get_topics():
    # 只返回前 10 个最活跃的主题
    active_topics = {k: v for k, v in list(topic_keywords.items())[:10]}
    return jsonify(active_topics)

@app.route('/api/poem/<int:poem_id>/reviews')
def get_poem_reviews(poem_id):
    reviews = Review.query.filter_by(poem_id=poem_id).all()
    result = []
    for r in reviews:
        user = User.query.get(r.user_id)
        result.append({
            "id": r.id,
            "user_id": user.username if user else "匿名",
            "rating": r.rating,
            "comment": r.comment
        })
    return jsonify(result)

@app.route('/api/poem/review', methods=['POST'])
def add_review():
    data = request.json
    username = data.get('username')
    poem_id = data.get('poem_id')
    rating = data.get('rating', 5)
    comment = data.get('comment')
    
    if not all([username, poem_id, comment]):
        return jsonify({"message": "缺失必要信息", "status": "error"}), 400
        
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "用户不存在", "status": "error"}), 404
        
    new_review = Review(
        user_id=user.id,
        poem_id=poem_id,
        rating=rating,
        comment=comment
    )
    db.session.add(new_review)
    db.session.commit()
    
    # 局部异步更新
    refresh_system_data()
    
    return jsonify({"message": "雅评已收录", "status": "success"})

def _get_user_preference_data(username):
    """提取获取用户偏好的核心逻辑 (内部使用)"""
    if df_data is None or lda_model is None:
        return None, 503
        
    user_rows = df_data[df_data['user_id'] == username]
    if len(user_rows) == 0:
        return None, 404

    user_dist = {}
    for idx in user_rows.index:
        dist = doc_topic_probs.get(idx, {})
        for tid, prob in dist.items():
            user_dist[tid] = user_dist.get(tid, 0) + prob
    
    total = sum(user_dist.values()) or 1
    preference = []
    for tid, score in user_dist.items():
        if tid in topic_keywords:
            preference.append({
                "topic_id": int(tid),
                "score": float(score / total),
                "keywords": topic_keywords[tid][:3]
            })
    
    preference.sort(key=lambda x: x['score'], reverse=True)
    preference = preference[:5]
    
    return {
        "user_id": username,
        "preference": preference,
        "top_interest": preference[0]['keywords'] if preference else ["通用"]
    }, 200

@app.route('/api/user_preference/<username>')
def get_user_preference(username):
    data, code = _get_user_preference_data(username)
    if code != 200:
        return jsonify({"error": "User or Model not found"}), code
    return jsonify(data)

@app.route('/api/recommend_personal/<username>')
def recommend_personal(username):
    data, code = _get_user_preference_data(username)
    if code != 200 or not data['preference']:
        return jsonify([])
    
    top_topic_id = data['preference'][0]['topic_id']
    return recommend_by_topic(top_topic_id)

@app.route('/api/recommend_one/<username>')
def recommend_one(username):
    """智能换诗：优先推荐符合口味的一首诗"""
    import random
    data, code = _get_user_preference_data(username)
    
    poem_obj = None
    reason = "随机选取的千古佳作"

    if code == 200 and data['preference']:
        top_topic_id = data['preference'][0]['topic_id']
        candidates = []
        # 在缓存分布中寻找匹配度高的诗
        for idx, dist in doc_topic_probs.items():
            if dist.get(top_topic_id, 0) > 0.2: # 匹配度阈值
                candidates.append(idx)
        
        if candidates:
            target_idx = random.choice(candidates[:20]) # 从前20个里抽
            row = df_data.loc[target_idx]
            poem_obj = Poem.query.filter_by(title=row['poem_title']).first()
            reason = f"因您对“{' '.join(data['top_interest'][:2])}”感兴趣而荐"

    if not poem_obj:
        all_count = Poem.query.count()
        if all_count > 0:
            poem_obj = Poem.query.offset(random.randrange(all_count)).first()

    if poem_obj:
        res = poem_obj.to_dict()
        res['recommend_reason'] = reason
        return jsonify(res)
    
    return jsonify({"error": "Poem list empty"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
