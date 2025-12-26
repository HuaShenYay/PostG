from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from models import db, User, Poem, Review
import pandas as pd
from sqlalchemy import text  # 修复 text 未定义的错误
from lda_analysis import train_lda_model
import os

app = Flask(__name__)
app.config.from_object(Config)

# 初始化插件
CORS(app)
db.init_app(app)

# --- 全局变量 ---
lda_model = None
vectorizer = None
# df_data 将不再存储CSV原始内容，而是存储从数据库读出的、包含 'processed_comment' 的 DataFrame
df_data = None
topic_keywords = {}

def init_db_and_model():
    """初始化数据库和模型"""
    global lda_model, vectorizer, df_data, topic_keywords
    
    with app.app_context():
        # 1. 确保数据库连接正常
        try:
            db.create_all()
            print("数据库连接正常。")
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return

        # 2. 从数据库读取评论数据用于训练 LDA
        # 我们需要联表查询：Review + User + Poem
        print("正在从数据库读取评论数据...")
        
        # 使用 pandas 读取 SQL
        # 构造 SQL 查询：取出 user_id (name), poem_title, rating, comment
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
        
        # 利用 pandas 的 read_sql 只需传入 sql 语句和 db.session.connection()
        # 注意: sqlalchemy 2.x 需要 connection()
        try:
             df_db = pd.read_sql(sql, db.session.connection())
        except Exception:
             # 兼容旧版本 sqlalchemy
             df_db = pd.read_sql(sql, db.engine)

        if len(df_db) == 0:
            print("警告：数据库中没有评论数据，LDA模型无法训练。请运行 import_data.py")
            return

        print(f"成功读取 {len(df_db)} 条评论数据，准备训练LDA...")
        
        # 3. 训练LDA模型
        # train_lda_model 本来是读CSV文件，现在我们把从数据库读出来的 df 传给它
        # 我们需要简单修改 lda_analysis.py 让它支持传入 DataFrame，或者我们在这里通过代码调用
        # 为了不改动 lda_analysis.py 太多，我们直接复用它的逻辑，但覆盖它的 load_data
        
        from lda_analysis import load_stopwords, preprocess_text
        from sklearn.feature_extraction.text import CountVectorizer
        from sklearn.decomposition import LatentDirichletAllocation

        # 预处理
        stopwords = load_stopwords()
        df_db['processed_comment'] = df_db['comment'].apply(lambda x: preprocess_text(str(x), stopwords))
        
        # 保存到全局变量，供推荐接口使用
        df_data = df_db
        
        # 向量化
        tf_vectorizer = CountVectorizer(max_df=0.95, min_df=2)
        tf = tf_vectorizer.fit_transform(df_db['processed_comment'])
        
        # 训练
        n_topics = 3
        print(f"开始训练LDA模型 (Topic={n_topics})...")
        lda = LatentDirichletAllocation(n_components=n_topics, max_iter=50,
                                        learning_method='online',
                                        learning_offset=50.,
                                        random_state=0)
        lda.fit(tf)
        
        # 保存模型
        lda_model = lda
        vectorizer = tf_vectorizer
        
        # 提取关键词
        feature_names = tf_vectorizer.get_feature_names_out()
        for topic_idx, topic in enumerate(lda.components_):
            top_features_ind = topic.argsort()[:-11:-1]
            top_features = [feature_names[i] for i in top_features_ind]
            topic_keywords[topic_idx] = top_features
            
        print("系统初始化完成！")

# 启动时初始化
init_db_and_model()

@app.route('/')
def hello_world():
    return 'Hello, MySQL + Poetry!'

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
    
    # 检查用户是否已存在
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

@app.route('/api/test')
def api_test():
    return jsonify({"message": "MySQL连接成功！LDA模型已就绪。", "status": "success"})

@app.route('/api/poems')
def get_poems():
    """从MySQL数据库获取诗歌"""
    # 查询所有诗歌
    poems = Poem.query.limit(20).all()
    return jsonify([p.to_dict() for p in poems])

@app.route('/api/topics')
def get_topics():
    return jsonify(topic_keywords)

@app.route('/api/users')
def get_users():
    """从MySQL获取用户列表"""
    users = User.query.with_entities(User.username).all()
    # users 是 [(u1,), (u2,)] 格式
    return jsonify([u[0] for u in users])

# ... (保留其他LDA相关的路由，稍后我们将把它们也改造成读数据库) ...
# 为了保证系统不崩，先复用之前的逻辑（读全局 df_data），混用一下数据库和内存

@app.route('/api/poem/<int:poem_id>/reviews')
def get_poem_reviews(poem_id):
    """获取某首诗歌的所有评论"""
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
    """发表新评论"""
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
    
    return jsonify({"message": "雅评已收录", "status": "success"})

@app.route('/api/user_preference/<username>')
def get_user_preference(username):
    # 注意：这里为了兼容之前的逻辑，参数名用了 username
    # 逻辑复用之前的 df_data (内存中的CSV)，因为LDA训练是基于那份数据的
    # 在真正完美的系统中，这里应该去查询 Review 表
    
    user_comments = df_data[df_data['user_id'] == username]['processed_comment']
    if len(user_comments) == 0:
        return jsonify({"error": "User not found"}), 404

    tf = vectorizer.transform(user_comments)
    doc_topic_dist = lda_model.transform(tf)
    user_topic_dist = doc_topic_dist.mean(axis=0)
    
    preference = []
    for topic_idx, score in enumerate(user_topic_dist):
        preference.append({
            "topic_id": topic_idx,
            "score": float(score),
            "keywords": topic_keywords[topic_idx][:3]
        })
    preference.sort(key=lambda x: x['score'], reverse=True)
    
    return jsonify({
        "user_id": username,
        "preference": preference,
        "top_interest": preference[0]['keywords']
    })

@app.route('/api/recommend_personal/<username>')
def recommend_personal(username):
    # 复用逻辑
    user_comments = df_data[df_data['user_id'] == username]['processed_comment']
    if len(user_comments) == 0: return jsonify([])
    
    tf = vectorizer.transform(user_comments)
    user_topic_dist = lda_model.transform(tf).mean(axis=0)
    top_topic_id = user_topic_dist.argmax()
    return recommend_by_topic(int(top_topic_id))

@app.route('/api/recommend/<int:topic_id>')
def recommend_by_topic(topic_id):
    if topic_id not in topic_keywords:
        return jsonify({"error": "Invalid topic id"}), 400
    
    doc_topic_dist = lda_model.transform(vectorizer.transform(df_data['processed_comment']))
    topic_probs = doc_topic_dist[:, topic_id]
    top_doc_indices = topic_probs.argsort()[:-6:-1]
    
    recommended_poems = []
    for idx in top_doc_indices:
        row = df_data.iloc[idx]
        recommended_poems.append({
            "title": row['poem_title'],
            "reason": f"匹配度: {topic_probs[idx]:.2f}",
            "related_comment": row['comment'][:50] + "..."
        })
    
    unique_recommendations = []
    seen_titles = set()
    for p in recommended_poems:
        if p['title'] not in seen_titles:
            unique_recommendations.append(p)
            seen_titles.add(p['title'])
            
    return jsonify(unique_recommendations)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
