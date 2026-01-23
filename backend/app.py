from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from models import db, User, Poem, Review
from datetime import datetime, timedelta
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
    
    # 在标题、作者、内容中进行模糊搜索
    results = Poem.query.filter(
        (Poem.title.ilike(f'%{query}%')) |
        (Poem.author.ilike(f'%{query}%')) |
        (Poem.content.ilike(f'%{query}%'))
    ).limit(20).all()
    
    # 为搜索结果添加推荐理由
    poems_with_reason = []
    for p in results:
        poem_dict = p.to_dict()
        poem_dict['recommend_reason'] = f"匹配搜索\"{query}\""
        poems_with_reason.append(poem_dict)
    
    return jsonify(poems_with_reason)

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

@app.route('/api/poem/<int:poem_id>/allusions')
def get_poem_allusions(poem_id):
    """获取诗歌的用典注释 (Real Data)"""
    poem = Poem.query.get(poem_id)
    if poem and poem.notes:
        try:
            return jsonify(json.loads(poem.notes))
        except:
            return jsonify([])
    return jsonify([])

@app.route('/api/poem/<int:poem_id>/helper')
def get_poem_helper(poem_id):
    """获取诗歌辅助理解信息 (Real Data)"""
    poem = Poem.query.get(poem_id)
    if not poem:
         return jsonify({
            "author_bio": "",
            "background": "",
            "appreciation": ""
        })
    
    return jsonify({
        "author_bio": poem.author_bio or "暂无作者生平信息",
        "background": f"[{poem.dynasty}]" if poem.dynasty else "",
        "appreciation": poem.appreciation or "暂无赏析"
    })

@app.route('/api/poem/<int:poem_id>/analysis')
def get_single_poem_analysis(poem_id):
    """获取单首诗的深度分析：格律矩阵与韵脚流转"""
    poem = Poem.query.get(poem_id)
    if not poem:
        return jsonify({"matrix": [], "rhymes": []})
        
    import re
    from pypinyin import pinyin, Style
    
    # 1. 声律矩阵 (Tonal Matrix)
    # 按行拆分内容
    lines = [l.strip() for l in re.split(r'[，。！？；\n]', poem.content) if l.strip()]
    matrix = []
    for line in lines:
        # 使用 TONE2 风格，声调数字总是在末尾
        line_pinyin = pinyin(line, style=Style.TONE3, neutral_tone_with_five=True)
        line_matrix = []
        for char, py in zip(line, line_pinyin):
            s = py[0]
            tone = "?"
            # 过滤非汉字
            if re.match(r'[\u4e00-\u9fa5]', char):
                if s and s[-1].isdigit():
                    t_num = int(s[-1])
                    if t_num in [1, 2]: tone = "平"
                    elif t_num in [3, 4, 5]: tone = "仄" # 5也是仄声（入声在普通话中多转为仄）
                else:
                    # 备用方案：如果 TONE3 没拿到数字，尝试 TONE2
                    s2 = pinyin(char, style=Style.TONE2)[0][0]
                    if s2 and s2[-1].isdigit():
                        t_num = int(s2[-1])
                        tone = "平" if t_num in [1, 2] else "仄"
            
            line_matrix.append({"char": char, "tone": tone})
        matrix.append(line_matrix)
        
    # 2. 韵脚流转 (Rhyme Flow)
    rhymes = []
    for idx, line in enumerate(lines):
        if not line: continue
        last_char = line[-1]
        # 获取不带声调的拼音作为韵部近似
        py_full = pinyin(last_char, style=Style.NORMAL)[0][0]
        # 简单的韵母提取（取最后一部分）
        vowels = "aeiouü"
        rhyme_part = py_full
        for i in range(len(py_full)):
            if py_full[i] in vowels:
                rhyme_part = py_full[i:]
                break
        
        rhymes.append({
            "line": idx + 1,
            "char": last_char,
            "rhyme": rhyme_part
        })
        
    # 3. 情感倾向分析 (Sentiment Profile)
    # Simple keyword-based sentiment for demonstration of "interesting" viz
    sentiment_dict = {
        "雄浑": ["大", "长", "云", "山", "河", "壮", "万", "天", "高"],
        "忧思": ["愁", "悲", "泪", "苦", "孤", "恨", "断", "老", "梦"],
        "闲适": ["悠", "闲", "醉", "卧", "月", "酒", "归", "眠", "静"],
        "清丽": ["花", "香", "翠", "色", "红", "绿", "秀", "春", "嫩"],
        "羁旅": ["客", "路", "远", "家", "乡", "雁", "征", "帆", "渡"]
    }
    sentiment_scores = {k: 10 for k in sentiment_dict} # Base 10
    for char in poem.content:
        for k, words in sentiment_dict.items():
            if char in words:
                sentiment_scores[k] += 15
    
    # 4. 为了平仄心跳图，需要整理一维序列
    tonal_chart_data = [] 
    char_labels = []
    
    if matrix:
        for row in matrix:
            for cell in row:
                char_labels.append(cell['char'])
                # 这里的 1 和 -1 用于 ECharts 绘图
                tonal_chart_data.append(1 if cell['tone'] == '平' else -1 if cell['tone'] == '仄' else 0)
    
    # Ensure some data even if parsing failed
    if not tonal_chart_data:
        tonal_chart_data = [0] * len(poem.content.replace('\n', ''))
        char_labels = list(poem.content.replace('\n', ''))

    return jsonify({
        "matrix": matrix,
        "rhymes": rhymes,
        "chart_data": {
            "tonal_sequence": tonal_chart_data,
            "char_labels": char_labels,
            "sentiment": [
                {"name": k, "value": v} for k, v in sentiment_scores.items()
            ]
        }
    })

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
    # 获取用户ID参数
    user_id = request.args.get('user_id')
    
    if user_id:
        # 个性化词云：基于用户偏好主题生成
        user = User.query.filter_by(username=user_id).first()
        if user and user.preference_topics:
            # 获取用户偏好主题
            preference = json.loads(user.preference_topics)
            processed_words = []
            
            # 遍历用户偏好的主题，生成关键词数据
            for p in preference:
                topic_id = p['topic_id']
                score = p['score']
                # 获取主题对应的关键词
                keywords = topic_keywords.get(topic_id, [])
                # 根据偏好分数生成权重
                weight = int(score * 100)
                # 将关键词按权重重复，生成词频
                processed_words.extend(keywords * weight)
            
            # 统计词频
            word_counts = Counter(processed_words)
            # 转换为 ECharts 需要的格式，取前 100 个高频词
            data = [{"name": w, "value": c} for w, c in word_counts.most_common(100)]
            return jsonify(data)
    
    # 若用户无偏好或未登录，返回空词云数据
    return jsonify([])

@app.route('/api/visual/stats')
def get_system_stats():
    """获取系统高级统计数据（多维雷达 + 桑基流向）"""
    # 获取用户ID参数
    user_id = request.args.get('user_id')
    
    # 1. 基础计数
    total_users = User.query.count()
    total_poems = Poem.query.count()
    total_reviews = Review.query.count()
    
    # 2. 准备数据：获取带有作者信息的评论主题分布
    if user_id:
        # 个性化：仅使用当前用户的评论数据
        user = User.query.filter_by(username=user_id).first()
        if user:
            sql = text("""
                SELECT p.author, r.topic_distribution 
                FROM reviews r
                JOIN poems p ON r.poem_id = p.id
                WHERE r.user_id = :user_id AND r.topic_distribution IS NOT NULL
            """)
            try:
                raw_data = db.session.connection().execute(sql, {'user_id': user.id}).fetchall()
            except:
                raw_data = []
        else:
            raw_data = []
    else:
        # 全局：使用所有评论数据
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

    # --- A. 雷达图数据：诗韵音律分析 (Rhythm & Tonal Analysis) ---
    # We will gather stats on Tonal Patterns (Ping vs Ze) and Rhythm Types
    
    # Base query for poems involved (either all or user-specific)
    if user_id:
        # User's history
        target_poems_query = db.session.query(Poem).join(Review).filter(Review.user_id == user.id)
    else:
        # System average (Up to 1000 poems for better coverage)
        target_poems_query = db.session.query(Poem).filter(Poem.tonal_summary != None).limit(1000)
        
    poems_list = target_poems_query.all()
    
    # Aggregators
    total_ping = 0
    total_ze = 0
    count_shi = 0
    count_ci = 0
    count_yuefu = 0
    total_chars = 0
    
    # Init map for Sankey
    author_topic_map = {}

    for p in poems_list:
        # Type count
        if p.rhythm_type == '词':
            count_ci += 1
        elif '府' in (p.rhythm_name or '') or '歌' in (p.rhythm_name or ''):
            count_yuefu += 1
        else:
            count_shi += 1
            
        # Tonal stats
        if p.tonal_summary:
            try:
                ts = json.loads(p.tonal_summary)
                total_ping += ts.get('ping', 0)
                total_ze += ts.get('ze', 0)
                total_chars += ts.get('total', 0)
            except:
                pass
        
        # Sankey Data Aggregation (Author -> Topic)
        # Iterate reviews for this poem to get topic distribution
        # Optimziation: If user_id is set, we only care about THAT user's reviews, 
        # but p.reviews has ALL. We should filter if generic.
        # Actually for 'System Stats' using all reviews of these sampled poems is fine.
        if p.reviews:
            for r in p.reviews:
                # If specific user requested, only partial filter? 
                # The query for poems was already filtered by user if user_id present.
                # But p.reviews relationship loads all. 
                # It's safer to just process all for the "Author Flow" or check user_id match if strict.
                # Let's keep it simple: Aggregate available reviews.
                if r.topic_distribution:
                    try:
                        dist = json.loads(r.topic_distribution)
                        author = p.author or "未知"
                        if author not in author_topic_map:
                            author_topic_map[author] = {}
                        for tid, prob in dist.items():
                            tid_int = int(tid)
                            author_topic_map[author][tid_int] = author_topic_map[author].get(tid_int, 0) + prob
                    except:
                        pass
                
    # Calculate Ratios
    # 1. Ping Ratio (Level Tone)
    # 2. Ze Ratio (Oblique Tone)
    # 3. Formality (Regulated verse vs irregular) - simple proxy via Shi vs Ci
    # 4. Melodic (Ci usually more melodic/varied)
    # 5. Density (Chars per poem avg - maybe not radar suitable, let's use 'Complexity')
    
    # Normalize to 0-100 scales approx
    if total_chars > 0:
        score_ping = (total_ping / total_chars) * 100 * 1.5 # Scale up a bit, usually around 50%
        score_ze = (total_ze / total_chars) * 100 * 1.5
    else:
        score_ping = 50
        score_ze = 50
        
    total_count = len(poems_list) or 1
    score_shi = (count_shi / total_count) * 100
    score_ci = (count_ci / total_count) * 100
    score_yuefu = (count_yuefu / total_count) * 100 * 2 # Boost smaller category
    
    radar_data = {
        "indicator": [
            {"name": "平声韵 (Level)", "max": 100},
            {"name": "仄声韵 (Oblique)", "max": 100},
            {"name": "格律 (Formal)", "max": 100},
            {"name": "词牌 (Lyrical)", "max": 100},
            {"name": "乐府 (Folk)", "max": 100}
        ],
        "value": [
            round(min(score_ping, 100), 1), 
            round(min(score_ze, 100), 1), 
            round(min(score_shi, 100), 1),
            round(min(score_ci, 100), 1),
            round(min(score_yuefu, 100), 1)
        ]
    }
    
    # --- B. 桑基图数据：作者 -> 主题流向 (Author-Topic Flow) ---
    # Keep existing Logic for Sankey as it uses Topics which are still valid and cool
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


# --- Global Analysis APIs ---

@app.route('/api/global/stats')
def get_global_stats():
    """获取全站统计数据"""
    try:
        # 基础统计
        total_users = User.query.count()
        total_poems = Poem.query.count()
        total_reviews = Review.query.count()
        
        # 扩展统计
        total_likes = db.session.query(func.sum(Poem.likes)).scalar() or 0
        total_views = db.session.query(func.sum(Poem.views)).scalar() or 0
        total_shares = db.session.query(func.sum(Poem.shares)).scalar() or 0
        
        # 平均互动率
        avg_engagement = round((total_likes + total_views + total_shares) / (total_poems * 3), 2) if total_poems > 0 else 0
        
        # 今日新增
        today = datetime.utcnow().date()
        today_users = User.query.filter(func.date(User.created_at) == today).count()
        today_reviews = Review.query.filter(func.date(Review.created_at) == today).count()
        
        return jsonify({
            "totalUsers": total_users,
            "totalPoems": total_poems,
            "totalReviews": total_reviews,
            "totalLikes": total_likes,
            "totalViews": total_views,
            "totalShares": total_shares,
            "avgEngagement": f"{avg_engagement * 100}%",
            "todayNewUsers": today_users,
            "todayReviews": today_reviews
        })
    except Exception as e:
        return jsonify({"error": f"获取统计数据失败: {str(e)}"}), 500

@app.route('/api/global/popular-poems')
def get_popular_poems():
    """获取热门诗歌排行"""
    try:
        time_range = request.args.get('time_range', 'week')
        
        # 根据时间范围过滤
        query = Poem.query
        if time_range == 'today':
            query = query.filter(func.date(Poem.created_at) == datetime.utcnow().date())
        elif time_range == 'week':
            week_ago = datetime.utcnow() - timedelta(days=7)
            query = query.filter(Poem.created_at >= week_ago)
        elif time_range == 'month':
            month_ago = datetime.utcnow() - timedelta(days=30)
            query = query.filter(Poem.created_at >= month_ago)
        
        # 获取所有符合条件的诗歌
        all_poems = query.all()
        
        # 按评论数排序（用户要求热门诗篇依赖评论数来排名）
        sorted_poems = sorted(all_poems, key=lambda p: len(p.reviews), reverse=True)
        popular_poems = sorted_poems[:10]
        
        result = []
        for poem in popular_poems:
            result.append({
                "id": poem.id,
                "title": poem.title,
                "dynasty": poem.dynasty,
                "author": poem.author,
                "likes": poem.likes,
                "review_count": len(poem.reviews),
                "views": poem.views,
                "shares": poem.shares
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"获取热门诗歌失败: {str(e)}"}), 500

@app.route('/api/global/theme-distribution')
def get_theme_distribution():
    """获取全站主题分布"""
    try:
        # 从所有评论中统计主题分布
        theme_counts = {}
        total_reviews = Review.query.filter(Review.topic_distribution.isnot(None)).count()
        
        for review in Review.query.filter(Review.topic_distribution.isnot(None)).all():
            if review.topic_distribution:
                topics = json.loads(review.topic_distribution)
                for topic_id, count in topics.items():
                    theme_name = topic_keywords.get(int(topic_id), ["未知"])[0]
                    theme_counts[theme_name] = theme_counts.get(theme_name, 0) + count
        
        # 转换为图表需要的格式
        result = []
        for theme, count in theme_counts.items():
            result.append({
                "name": theme,
                "value": count
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"获取主题分布失败: {str(e)}"}), 500

@app.route('/api/global/dynasty-distribution')
def get_dynasty_distribution():
    """获取朝代分布统计"""
    try:
        dynasty_stats = {}
        total_poems = Poem.query.count()
        
        # 统计各朝代诗歌数量
        for poem in Poem.query.all():
            dynasty = poem.dynasty or '其他'
            dynasty_stats[dynasty] = dynasty_stats.get(dynasty, 0) + 1
        
        # 转换为图表格式，按常见朝代排序
        dynasty_order = ['唐', '宋', '元', '明', '清', '先秦', '汉', '魏晋', '南北朝', '其他']
        result = []
        for dynasty in dynasty_order:
            if dynasty in dynasty_stats:
                result.append({
                    "name": dynasty,
                    "value": dynasty_stats[dynasty]
                })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"获取朝代分布失败: {str(e)}"}), 500

@app.route('/api/global/trends')
def get_global_trends():
    """获取全站趋势数据"""
    try:
        period = request.args.get('period', 'week')
        
        # 生成最近7天的日期
        dates = []
        user_counts = []
        review_counts = []
        poem_counts = []
        
        if period == 'week':
            days = 7
        elif period == 'month':
            days = 30
        else:
            days = 90
        
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i)
            dates.append(date.strftime('%m-%d'))
            
            # 统计该日期的数据
            day_users = User.query.filter(func.date(User.created_at) == date.date()).count()
            day_reviews = Review.query.filter(func.date(Review.created_at) == date.date()).count()
            day_poems = Poem.query.filter(func.date(Poem.created_at) == date.date()).count()
            
            user_counts.append(day_users)
            review_counts.append(day_reviews)
            poem_counts.append(day_poems)
        
        return jsonify({
            "dates": dates[::-1],  # 反转使最新日期在前
            "users": user_counts[::-1],
            "reviews": review_counts[::-1],
            "poems": poem_counts[::-1]
        })
    except Exception as e:
        return jsonify({"error": f"获取趋势数据失败: {str(e)}"}), 500

@app.route('/api/global/wordcloud')
def get_global_wordcloud():
    """获取全站词云数据"""
    try:
        # 获取所有评论内容进行词频统计
        all_comments = Review.query.with_entities(Review.comment).all()
        
        # 合并所有评论文本
        all_text = ' '.join([r.comment for r in all_comments if r.comment])
        
        # 简单分词和统计
        import re
        words = re.findall(r'[\u4e00-\u9fa5]+', all_text)
        word_counts = Counter(words)
        
        # 过滤停用词和短词
        stopwords = ['的', '了', '是', '在', '有', '和', '就', '不', '人', '都', '一', '个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这']
        filtered_words = {word: count for word, count in word_counts.items() 
                        if len(word) > 1 and word not in stopwords}
        
        # 取前100个高频词
        top_words = sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:100]
        
        result = [{"name": word, "value": count} for word, count in top_words]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"获取词云数据失败: {str(e)}"}), 500

# --- User Profile & Analysis APIs ---

@app.route('/api/user/<username>/stats')
def get_user_profile_stats(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"totalReads": 0, "avgRating": 0, "reviewCount": 0, "activeDays": 0})
    
    reviews = Review.query.filter_by(user_id=user.id).all()
    review_count = len(reviews)
    avg_rating = sum([r.rating for r in reviews]) / review_count if review_count > 0 else 0
    
    # Simple active days count based on created_at (mock for real login tracking)
    active_days = (datetime.utcnow() - user.created_at).days + 1
    
    # Reads: using reviews as proxy for interaction
    total_reads = review_count * 3 + 5 # Mocking some extra views
    
    return jsonify({
        "totalReads": total_reads,
        "avgRating": round(avg_rating, 1),
        "reviewCount": review_count,
        "activeDays": active_days
    })

@app.route('/api/user/<username>/preferences')
def get_user_prefs_api(username):
    user = User.query.filter_by(username=username).first()
    if not user or not user.preference_topics:
        # Default/Initial fallback
        return jsonify({"preferences": [
            {"topic_name": "山水田园", "percentage": 40, "color": "#cf3f35"},
            {"topic_name": "思乡情怀", "percentage": 35, "color": "#bfa46f"},
            {"topic_name": "豪迈边塞", "percentage": 25, "color": "#1a1a1a"}
        ]})
    
    prefs = json.loads(user.preference_topics)
    formatted = []
    colors = ["#cf3f35", "#bfa46f", "#1a1a1a", "#1b1a8a", "#1b8a1a"]
    
    for i, p in enumerate(prefs[:5]):
        tid = p['topic_id']
        keywords = topic_keywords.get(tid, ["通用"])
        formatted.append({
            "topic_id": tid,
            "topic_name": keywords[0],
            "percentage": int(p['score'] * 100),
            "color": colors[i % len(colors)]
        })
    return jsonify({"preferences": formatted})

@app.route('/api/user/<username>/form-stats')
def get_user_form_stats(username):
    """个人格律偏好：五律、七律、五绝、七绝等"""
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify([])
        
    reviews = Review.query.filter_by(user_id=user.id).all()
    if not reviews:
        # Fallback to general favorites
        return jsonify([
            {"name": "七言律诗", "value": 35},
            {"name": "五言律诗", "value": 25},
            {"name": "七言绝句", "value": 20},
            {"name": "五言绝句", "value": 15},
            {"name": "宋词/其他", "value": 5}
        ])
        
    form_counts = Counter()
    for r in reviews:
        p = Poem.query.get(r.poem_id)
        if p and p.rhythm_name:
            # 统一格律称谓
            name = p.rhythm_name
            if "五" in name and "律" in name: form_counts["五律"] += 1
            elif "七" in name and "律" in name: form_counts["七律"] += 1
            elif "五" in name and "绝" in name: form_counts["五绝"] += 1
            elif "七" in name and "绝" in name: form_counts["七绝"] += 1
            elif p.rhythm_type == "词": form_counts["词/曲"] += 1
            else: form_counts["其他"] += 1
            
    if not form_counts:
         return jsonify([{"name": "七律", "value": 40}, {"name": "五律", "value": 30}, {"name": "其他", "value": 30}])

    return jsonify([{"name": k, "value": v} for k, v in form_counts.items()])

@app.route('/api/user/<username>/time-analysis')
def get_user_time_analysis(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"insights": []})
        
    reviews = Review.query.filter_by(user_id=user.id).all()
    if not reviews:
        # Generic fallback
        return jsonify({
            "insights": [
                {"time": "子时", "value": 15}, {"time": "卯时", "value": 10},
                {"time": "午时", "value": 40}, {"time": "酉时", "value": 85},
                {"time": "亥时", "value": 30}
            ]
        })
        
    # Mapping hour to Shichen
    shichen_map = {
        0: "子时", 1: "丑时", 2: "丑时", 3: "寅时", 4: "寅时", 
        5: "卯时", 6: "卯时", 7: "辰时", 8: "辰时", 9: "巳时", 10: "巳时", 
        11: "午时", 12: "午时", 13: "未时", 14: "未时", 15: "申时", 16: "申时", 
        17: "酉时", 18: "酉时", 19: "戌时", 20: "戌时", 21: "亥时", 22: "亥时", 23: "子时"
    }
    
    counts = Counter()
    for r in reviews:
        if r.created_at:
            h = r.created_at.hour
            counts[shichen_map.get(h, "未知")] += 1
            
    # Ordered display
    ordered_shichen = ["子时", "卯时", "午时", "酉时", "亥时"]
    insights = [{"time": s, "value": counts.get(s, 0)} for s in ordered_shichen]
    
    return jsonify({"insights": insights})

@app.route('/api/user/<username>/recommendations')
def get_user_recommendations_v2(username):
    # Use existing internal logic
    data, code = _get_user_preference_data(username)
    if code != 200 or not data['preference']:
        # Fallback to generic
        poems = Poem.query.limit(3).all()
        return jsonify({"poems": [{
            "id": p.id,
            "title": p.title,
            "author": p.author,
            "content": p.content,
            "reason": "为您初步挑选的佳作"
        } for p in poems]})
    
    top_topic_id = data['preference'][0]['topic_id']
    # Use the logic from recommend_by_topic but return formatted for list
    recs = recommend_by_topic(top_topic_id).get_json()
    
    result = []
    for r in recs:
        p = Poem.query.filter_by(title=r['title']).first()
        if p:
            result.append({
                "id": p.id,
                "title": p.title,
                "author": p.author,
                "content": p.content,
                "reason": r['reason']
            })
            
    return jsonify({"poems": result[:4]})

@app.route('/api/user/<username>/wordcloud')
def get_user_wordcloud(username):
    """个人雅评关键词词云"""
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify([])
        
    reviews = Review.query.filter_by(user_id=user.id).all()
    if not reviews:
        # Fallback to preference keywords from LDA
        return get_wordcloud_data() # reuse global but with user_id arg from request
        
    all_comments = " ".join([r.comment for r in reviews])
    
    import jieba
    stopwords = load_stopwords()
    words = jieba.cut(all_comments)
    filtered = [w for w in words if len(w) > 1 and w not in stopwords]
    
    word_counts = Counter(filtered)
    return jsonify([{"name": k, "value": v} for k, v in word_counts.most_common(50)])

if __name__ == '__main__':
    # 仅在 Flask 热重载的子进程中运行初始化逻辑，避免跑两遍
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        init_db_and_model()
    
    app.run(debug=True, port=5000)
