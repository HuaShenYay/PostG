from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from models import db, User, Poem, Review
import pandas as pd
from sqlalchemy import text
import os
from lda_analysis import train_lda_model, load_stopwords, preprocess_text, save_lda_model, load_lda_model
import json
from collections import Counter
from sqlalchemy import func

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

def sync_global_cache():
    """同步数据库数据到全局变量 df_data"""
    global df_data, topic_keywords, lda_model, dictionary
    
    # 尝试加载模型元数据（如果内存中没有）
    if not topic_keywords:
        _, _, topic_keywords = load_lda_model()

    sql = text("""
        SELECT 
            u.username as user_id, 
            p.title as poem_title, 
            r.rating, 
            r.comment,
            r.id as review_id,
            r.topic_distribution
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        JOIN poems p ON r.poem_id = p.id
    """)
    try:
        df_data = pd.read_sql(sql, db.session.connection())
    except Exception:
        df_data = pd.read_sql(sql, db.engine)

def get_all_reviews_df():
    """获取全量评论的 DataFrame 供训练使用"""
    sql = text("""
        SELECT u.username as user_id, p.title as poem_title, r.rating, r.comment 
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        JOIN poems p ON r.poem_id = p.id
    """)
    try:
        return pd.read_sql(sql, db.session.connection())
    except Exception:
        return pd.read_sql(sql, db.engine)

def refresh_system_data():
    """
    按需增量刷新：仅在有新评论时才激活 LDA。
    如果没有新评论，只同步缓存，不进行任何模型计算。
    """
    global lda_model, dictionary, df_data, topic_keywords
    
    with app.app_context():
        # 1. 检查是否有未处理的新评论
        new_count = Review.query.filter(Review.topic_distribution == None).count()
        
        # 2. 如果没有新内容，仅同步全局缓存以便推荐系统正常工作
        if new_count == 0:
            sync_global_cache()
            print(">>> 检查完毕：无新增评论内容，跳过模型计算。")
            return

        # 3. 发现新内容，确保模型已加载
        if lda_model is None:
            lda_model, dictionary, topic_keywords = load_lda_model()
        
        # 4. 如果模型仍为空，尝试全量训练（仅针对第一次冷启动）
        if lda_model is None:
            df_all = get_all_reviews_df()
            if len(df_all) >= 3:
                print(">>> 未发现模型文件，正在执行初始化全量训练...")
                lda_model, dictionary, _, topic_keywords = train_lda_model(df_all)
                if lda_model:
                    save_lda_model(lda_model, dictionary, topic_keywords)
            else:
                sync_global_cache()
                return

        # 5. 执行增量分析：对新评论推断主题分布
        print(f">>> 发现 {new_count} 条新评论，仅对这些内容进行 LDA 主题识别...")
        new_reviews = Review.query.filter(Review.topic_distribution == None).all()
        stopwords = load_stopwords()
        affected_user_ids = set()
        
        for r in new_reviews:
            tokens = preprocess_text(str(r.comment), stopwords)
            if tokens:
                bow = dictionary.doc2bow(tokens)
                dist = dict(lda_model[bow])
                # 将推断结果存入数据库
                r.topic_distribution = json.dumps({str(k): float(v) for k, v in dist.items()})
                affected_user_ids.add(r.user_id)
        
        db.session.commit()

        # 6. 【重点】仅针对有新评论的用户更新画像
        for uid in affected_user_ids:
            update_user_preference(uid)
            print(f"  - 用户ID {uid} 的偏好画像已重新生成")
        
        # 7. 更新全局缓存
        sync_global_cache()
        print(">>> 增量分析与画像更新已完成。")

def update_user_preference(user_id):
    """根据用户的历史评论分布，计算并持久化用户偏好"""
    reviews = Review.query.filter(Review.user_id == user_id, Review.topic_distribution != None).all()
    if not reviews:
        return
        
    user_dist = {}
    for r in reviews:
        dist = json.loads(r.topic_distribution)
        for tid, prob in dist.items():
            user_dist[tid] = user_dist.get(tid, 0) + prob
            
    total = sum(user_dist.values()) or 1
    preference = []
    for tid, score in user_dist.items():
        preference.append({
            "topic_id": int(tid),
            "score": float(score / total)
        })
    
    # 按得分排序
    preference.sort(key=lambda x: x['score'], reverse=True)
    
    user = User.query.get(user_id)
    if user:
        user.preference_topics = json.dumps(preference)
        db.session.commit()

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

@app.route('/api/poems')
def get_poems():
    poems = Poem.query.limit(20).all()
    return jsonify([p.to_dict() for p in poems])

@app.route('/api/search_poems')
def search_poems():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    # 在标题、作者、内容中进行模糊搜索
    results = Poem.query.filter(
        (Poem.title.ilike(f'%{query}%')) |
        (Poem.author.ilike(f'%{query}%')) |
        (Poem.content.ilike(f'%{query}%'))
    ).limit(20).all()
    
    return jsonify([p.to_dict() for p in results])

@app.route('/api/topics')
def get_topics():
    # 返回所有主题
    return jsonify(topic_keywords)

@app.route('/api/save_initial_preferences', methods=['POST'])
def save_initial_preferences():
    """保存新用户选择的初始偏好主题"""
    data = request.json
    username = data.get('username')
    selected_topics = data.get('selected_topics', [])
    
    if not username:
        return jsonify({"message": "用户名不能为空", "status": "error"}), 400
    
    if not selected_topics:
        return jsonify({"message": "请至少选择一个主题", "status": "error"}), 400
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "用户不存在", "status": "error"}), 404
    
    # 将用户选择的主题转换为偏好格式
    # 为每个选中的主题分配较高的初始分数
    preference = []
    for i, topic_id in enumerate(selected_topics):
        # 根据选择顺序分配权重，第一个选择的权重最高
        weight = 1.0 - (i * 0.15)  # 递减权重
        preference.append({
            "topic_id": int(topic_id),
            "score": max(weight, 0.1)
        })
    
    # 按得分排序
    preference.sort(key=lambda x: x['score'], reverse=True)
    
    # 保存到数据库
    user.preference_topics = json.dumps(preference)
    db.session.commit()
    
    return jsonify({
        "message": "偏好设置成功",
        "status": "success",
        "preference": preference
    })

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
    user = User.query.filter_by(username=username).first()
    if not user:
        return None, 404
    
    # 优先从数据库读取已持久化的画像
    if user.preference_topics:
        preference = json.loads(user.preference_topics)
        # 补全关键词信息
        for p in preference:
            tid = p['topic_id']
            p['keywords'] = topic_keywords.get(tid, ["未知"])[:3]
        
        return {
            "user_id": username,
            "preference": preference,
            "top_interest": preference[0]['keywords'] if preference else ["通用"]
        }, 200

    # 兜底：如果数据库没有（比如刚迁移完），尝试从 df_data 现场计算一次
    if df_data is None:
        return None, 503
        
    user_rows = df_data[df_data['user_id'] == username]
    if len(user_rows) == 0:
        return None, 404

    user_dist = {}
    for _, row in user_rows.iterrows():
        dist_str = row.get('topic_distribution')
        if dist_str:
            dist = json.loads(dist_str)
            for tid, prob in dist.items():
                user_dist[tid] = user_dist.get(tid, 0) + prob
    
    total = sum(user_dist.values()) or 1
    preference = []
    for tid, score in user_dist.items():
        if int(tid) in topic_keywords:
            preference.append({
                "topic_id": int(tid),
                "score": float(score / total),
                "keywords": topic_keywords[int(tid)][:3]
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
        return jsonify({
            "user_id": username,
            "preference": [],
            "top_interest": ["通用"]
        })
    return jsonify(data)

@app.route('/api/recommend_personal/<username>')
def recommend_personal(username):
    data, code = _get_user_preference_data(username)
    if code != 200 or not data['preference']:
        return jsonify([])
    
    top_topic_id = data['preference'][0]['topic_id']
    return recommend_by_topic(top_topic_id)

@app.route('/api/recommend/<int:topic_id>')
def recommend_by_topic(topic_id):
    if df_data is None:
        return jsonify([])
    
    # 混合打分逻辑：LDA 匹配度 (70%) + 用户评价评分 (30%)
    scores = []
    for idx, row in df_data.iterrows():
        dist_str = row.get('topic_distribution')
        topic_prob = 0
        if dist_str:
            dist = json.loads(dist_str)
            topic_prob = dist.get(str(topic_id), 0)
        
        # 混合评分
        hybrid_score = topic_prob * 0.7 + (row['rating'] / 5.0) * 0.3
        scores.append((idx, hybrid_score))
    
    # 按得分排列
    scores.sort(key=lambda x: x[1], reverse=True)
    
    recommended_poems = []
    seen_titles = set()
    for idx, score in scores:
        if len(recommended_poems) >= 6: break
        row = df_data.loc[idx]
        if row['poem_title'] not in seen_titles:
            recommended_poems.append({
                "title": row['poem_title'],
                "reason": f"文脉匹配度: {score:.2f}",
                "related_comment": row['comment'][:50] + "..."
            })
            seen_titles.add(row['poem_title'])
            
    return jsonify(recommended_poems)

@app.route('/api/recommend_one/<username>')
def recommend_one(username):
    """智能换诗：增加多样性，避免重复，定期推荐未看过的诗歌"""
    import random
    current_id = request.args.get('current_id', type=int)
    skip_count = request.args.get('skip_count', 0, type=int)
    data, code = _get_user_preference_data(username)
    
    poem_obj = None
    reason = "随机选取的千古佳作"

    # 每5次推荐一次未被任何用户看过的诗歌，拓展用户视野
    if skip_count > 0 and skip_count % 5 == 0:
        # 查找所有诗歌ID
        all_poem_ids = [p.id for p in Poem.query.all()]
        # 查找所有被评论过的诗歌ID
        reviewed_poem_ids = [r.poem_id for r in Review.query.all()]
        # 找出未被看过的诗歌
        unseen_poem_ids = list(set(all_poem_ids) - set(reviewed_poem_ids))
        
        if unseen_poem_ids:
            # 随机选择一首未被看过的诗歌
            poem_obj = Poem.query.filter(Poem.id.in_(unseen_poem_ids)).first()
            if poem_obj:
                reason = "为您推荐一首尚未被发现的佳作"
        
        # 如果没有未被看过的诗歌，继续使用常规推荐逻辑

    # 如果没有推荐到诗歌，使用常规推荐逻辑
    if not poem_obj:
        # 如果有画像，尝试"加权随机"选择一个主题，增加多样性
        if code == 200 and data['preference']:
            prefs = data['preference']
            # 权重分配：70% 概率抽第一偏好，20% 抽第二，10% 抽第三（如果有的话）
            dice = random.random()
            if dice < 0.7 or len(prefs) < 2:
                target_pref = prefs[0]
            elif dice < 0.9 or len(prefs) < 3:
                target_pref = prefs[1]
            else:
                target_pref = prefs[2]
                
            target_topic_id = target_pref['topic_id']
            keywords = " · ".join(target_pref['keywords'][:2])
            
            # 寻找候选集
            candidates = []
            for idx, row in df_data.iterrows():
                dist_str = row.get('topic_distribution')
                if not dist_str:
                    continue
                dist = json.loads(dist_str)
                
                # 排除当前正在看的这首
                p = Poem.query.filter_by(title=row['poem_title']).first()
                if p and p.id == current_id:
                    continue
                    
                if dist.get(str(target_topic_id), 0) > 0.15: # 降低一点点阈值，扩大池子
                    candidates.append(p)
            
            if candidates:
                # 过滤掉 None
                candidates = [c for c in candidates if c]
                if candidates:
                    poem_obj = random.choice(candidates)
                    reason = f"因您对\"{keywords}\"感兴趣而荐"

        # 兜底：如果没抽到或者没画像，彻底随机
        if not poem_obj:
            query = Poem.query
            if current_id:
                query = query.filter(Poem.id != current_id)
            
            all_count = query.count()
            if all_count > 0:
                poem_obj = query.offset(random.randrange(all_count)).first()

    if poem_obj:
        res = poem_obj.to_dict()
        res['recommend_reason'] = reason
        return jsonify(res)
    
    return jsonify({"error": "Poem list empty"}), 404

# --- 可视化相关 API ---

@app.route('/api/visual/wordcloud')
def get_wordcloud_data():
    """生成评论词云数据"""
    # 获取所有评论
    reviews = Review.query.all()
    all_comments = [r.comment for r in reviews if r.comment]
    
    stopwords = load_stopwords()
    processed_words = []
    
    for comment in all_comments:
        # 使用 lda_analysis 中定义的预处理（分词+去停用词）
        words = preprocess_text(comment, stopwords)
        processed_words.extend(words)
        
    # 统计词频
    word_counts = Counter(processed_words)
    
    # 转换为 ECharts 需要的格式 [{"name": "词", "value": 频率}, ...]
    # 取前 100 个高频词
    data = [{"name": w, "value": c} for w, c in word_counts.most_common(100)]
    
    return jsonify(data)

@app.route('/api/visual/stats')
def get_system_stats():
    """获取系统高级统计数据（多维雷达 + 桑基流向）"""
    
    # 1. 基础计数
    total_users = User.query.count()
    total_poems = Poem.query.count()
    total_reviews = Review.query.count()
    
    # 2. 准备数据：获取带有作者信息的评论主题分布
    # 我们需要关联 poems 表获取作者
    sql = text("""
        SELECT p.author, r.topic_distribution 
        FROM reviews r
        JOIN poems p ON r.poem_id = p.id
        WHERE r.topic_distribution IS NOT NULL
    """)
    try:
        raw_data = db.session.connection().execute(sql).fetchall()
    except:
        raw_data = []

    # 全局主题缓存（确保 loaded）
    global topic_keywords, lda_model, dictionary
    if not topic_keywords:
        lda_model, dictionary, topic_keywords = load_lda_model()
    
    # 如果还是空的（没训练过），给点假数据防止崩图
    if not topic_keywords:
        return jsonify({
            "counts": {"users": total_users, "poems": total_poems, "reviews": total_reviews},
            "radar_data": [],
            "sankey_data": {"nodes": [], "links": []}
        })

    # --- A. 雷达图数据：系统的主题倾向 (System Topic Profile) ---
    # 统计所有评论中，各个 Topic 的总权重
    topic_weights = {}
    
    # --- B. 桑基图数据：作者 -> 主题流向 (Author-Topic Flow) ---
    # 统计 {Author: {TopicID: Weight}}
    author_topic_map = {}
    
    for row in raw_data:
        author = row[0]
        dist = json.loads(row[1])
        
        if author not in author_topic_map:
            author_topic_map[author] = {}
            
        for tid, prob in dist.items():
            tid_int = int(tid)
            # 全局累加
            topic_weights[tid_int] = topic_weights.get(tid_int, 0) + prob
            # 作者累加
            author_topic_map[author][tid_int] = author_topic_map[author].get(tid_int, 0) + prob
            
    # 处理雷达数据：取权重最高的 6 个主题
    sorted_topics = sorted(topic_weights.items(), key=lambda x: x[1], reverse=True)[:6]
    radar_indicator = []
    radar_values = []
    
    max_val = sorted_topics[0][1] if sorted_topics else 100
    
    for tid, weight in sorted_topics:
        # 获取该主题的代表词 (前2个)
        kw = topic_keywords.get(tid, ["未知"])[0] 
        label = f"主题{tid}-{kw}" # 如 "主题1-明月"
        radar_indicator.append({"name": label, "max": max_val})
        radar_values.append(weight)
        
    radar_data = {
        "indicator": radar_indicator,
        "value": radar_values
    }
    
    # 处理桑基数据：Top 5 作者 -> Top 5 关联主题
    # 1. 找出 Top Authors
    sorted_authors = sorted(author_topic_map.items(), 
                          key=lambda item: sum(item[1].values()), 
                          reverse=True)[:8] # 取前8位诗人
                          
    sankey_nodes = []
    sankey_links = []
    seen_nodes = set()
    
    for author, t_map in sorted_authors:
        if author not in seen_nodes:
            sankey_nodes.append({"name": author})
            seen_nodes.add(author)
            
        # 该作者权重最高的 3 个主题
        top_t_for_author = sorted(t_map.items(), key=lambda x: x[1], reverse=True)[:3]
        
        for tid, w in top_t_for_author:
            kw = topic_keywords.get(tid, ["未知"])[0]
            topic_node_name = f"意象：{kw}"
            
            if topic_node_name not in seen_nodes:
                sankey_nodes.append({"name": topic_node_name})
                seen_nodes.add(topic_node_name)
                
            sankey_links.append({
                "source": author,
                "target": topic_node_name,
                "value": round(w, 2)
            })
            
    return jsonify({
        "counts": {
            "users": total_users,
            "poems": total_poems,
            "reviews": total_reviews
        },
        "radar_data": radar_data,
        "sankey_data": {
            "nodes": sankey_nodes,
            "links": sankey_links
        }
    })


if __name__ == '__main__':
    # 仅在 Flask 热重载的子进程中运行初始化逻辑，避免跑两遍
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        init_db_and_model()
    
    app.run(debug=True, port=5000)
