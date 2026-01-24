#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化推荐更新系统

功能：
1. 监听数据库变更，实时检测新诗歌插入
2. 新诗歌入库后30秒内启动推荐更新流程
3. 为所有注册用户重新计算个性化推荐
4. 增量计算优化，减少重复计算
5. 完善的日志记录和失败重试机制
6. 性能监控，确保系统在可接受时间内完成

作者：诗云团队
日期：2024
"""

import threading
import time
import json
import logging
import traceback
from datetime import datetime, timedelta
from collections import Counter
from functools import wraps
import psutil
import os

from flask import Flask, current_app
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from config import Config
from models import db, User, Poem, Review
import pandas as pd


# ==================== 配置 ====================

class RecommendationConfig:
    """推荐系统配置"""
    
    # 触发延迟时间（秒）
    TRIGGER_DELAY = 30
    
    # 最大处理时间（秒）
    MAX_PROCESSING_TIME = 300  # 5分钟
    
    # 资源占用阈值
    CPU_THRESHOLD = 80.0  # 百分比
    MEMORY_THRESHOLD = 80.0  # 百分比
    
    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY = 60  # 秒
    
    # 批处理大小
    BATCH_SIZE = 50
    
    # 日志文件
    LOG_FILE = 'logs/recommendation_update.log'


# ==================== 日志系统 ====================

class RecommendationLogger:
    """推荐更新日志记录器"""
    
    def __init__(self):
        self.log_dir = 'logs'
        self.log_file = RecommendationConfig.LOG_FILE
        
        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('Recommendation')
    
    def log_update_start(self, trigger_type, poem_id=None):
        """记录更新开始"""
        self.logger.info(f"🔄 推荐更新开始 - 触发类型: {trigger_type}" + 
                        (f", 诗歌ID: {poem_id}" if poem_id else ""))
    
    def log_update_progress(self, current, total, elapsed_time):
        """记录更新进度"""
        progress = (current / total) * 100 if total > 0 else 0
        self.logger.info(f"📊 更新进度: {current}/{total} ({progress:.1f}%), " +
                        f"耗时: {elapsed_time:.2f}秒")
    
    def log_update_success(self, users_processed, poems_count, elapsed_time):
        """记录更新成功"""
        self.logger.info(f"✅ 推荐更新成功 - 处理用户: {users_processed}, " +
                        f"诗歌数: {poems_count}, 总耗时: {elapsed_time:.2f}秒")
    
    def log_update_failure(self, error, retry_count=0):
        """记录更新失败"""
        self.logger.error(f"❌ 推荐更新失败 - 错误: {error}, 重试次数: {retry_count}")
        self.logger.error(f"堆栈跟踪: {traceback.format_exc()}")
    
    def log_performance_metrics(self, cpu_usage, memory_usage, duration):
        """记录性能指标"""
        self.logger.info(f"📈 性能指标 - CPU: {cpu_usage:.1f}%, " +
                        f"内存: {memory_usage:.1f}%, 耗时: {duration:.2f}秒")
    
    def get_recent_logs(self, hours=24):
        """获取最近的日志"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                logs = f.readlines()
            
            # 过滤最近 hours 小时的日志
            cutoff = datetime.now() - timedelta(hours=hours)
            recent_logs = []
            for log in logs:
                if ' - ' in log:
                    timestamp_str = log.split(' - ')[0]
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        if timestamp >= cutoff:
                            recent_logs.append(log.strip())
                    except:
                        recent_logs.append(log.strip())
            
            return recent_logs[-100:]  # 返回最近100条
        except:
            return []


# ==================== 性能监控 ====================

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.start_time = None
        self.cpu_samples = []
        self.memory_samples = []
    
    def start_monitoring(self):
        """开始监控"""
        self.start_time = datetime.now()
        self.cpu_samples = []
        self.memory_samples = []
    
    def sample_resources(self):
        """采样资源使用"""
        try:
            process = psutil.Process(os.getpid())
            cpu = process.cpu_percent()
            memory = process.memory_percent()
            
            self.cpu_samples.append(cpu)
            self.memory_samples.append(memory)
            
            return cpu, memory
        except:
            return 0, 0
    
    def get_final_metrics(self):
        """获取最终性能指标"""
        if not self.start_time:
            return 0, 0, 0
        
        duration = (datetime.now() - self.start_time).total_seconds()
        
        avg_cpu = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0
        avg_memory = sum(self.memory_samples) / len(self.memory_samples) if self.memory_samples else 0
        
        return avg_cpu, avg_memory, duration
    
    def check_thresholds(self):
        """检查是否超出阈值"""
        avg_cpu, avg_memory, _ = self.get_final_metrics()
        
        return {
            'cpu_exceeded': avg_cpu > RecommendationConfig.CPU_THRESHOLD,
            'memory_exceeded': avg_memory > RecommendationConfig.MEMORY_THRESHOLD,
            'cpu_usage': avg_cpu,
            'memory_usage': avg_memory
        }


# ==================== 增量推荐计算 ====================

# ==================== 增量推荐计算 ====================
from bertopic_analysis import load_bertopic_model, predict_topic

# ==================== 增量推荐计算 ====================
from bertopic_analysis import load_bertopic_model, predict_topic, get_document_vector, batch_get_vectors
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class IncrementalRecommender:
    """基于主题向量的协同过滤推荐器 (Topic Vector CF)"""
    
    def __init__(self):
        self.logger = RecommendationLogger()
        self.monitor = PerformanceMonitor()
        self.bertopic_model = load_bertopic_model()
        self.topic_matrix = None # 诗歌主题向量矩阵 (n_poems, vector_dim)
        self.poem_id_map = {}    # poem_id -> matrix_index
        self.poem_ids = []       # [poem_id1, poem_id2, ...]
        
        self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saved_models', 'vector_cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 预加载向量矩阵
        self._build_poem_vector_matrix()

    def update_user_preference(self, user_id):
        """分析用户所有评论，更新用户偏好主题文本 (Restored from previous version)"""
        reviews = Review.query.filter_by(user_id=user_id).all()
        if not reviews:
            return ""
        
        # 统计用户评论中出现的主题名频率
        topic_counts = Counter()
        for r in reviews:
            if r.topic_names:
                names = r.topic_names.split(',')
                topic_counts.update(names)
        
        if not topic_counts:
            return ""
        
        # 获取最匹配的Top 3主题作为偏好描述
        top_topics = [t for t, _ in topic_counts.most_common(3)]
        return ",".join(top_topics)
    
    def _build_poem_vector_matrix(self):
        """构建全量诗歌向量矩阵（支持缓存加载）"""
        if not self.bertopic_model:
            return
            
        with current_app.app_context():
            poems = Poem.query.all()
            if not poems:
                return
            
            self.poem_ids = [p.id for p in poems]
            self.poem_id_map = {pid: idx for idx, pid in enumerate(self.poem_ids)}
            
            # 尝试从缓存加载
            matrix_path = os.path.join(self.cache_dir, 'topic_matrix.npy')
            ids_path = os.path.join(self.cache_dir, 'poem_ids.json')
            
            # 检查缓存是否有效 (ID列表匹配)
            cache_valid = False
            if os.path.exists(matrix_path) and os.path.exists(ids_path):
                try:
                    with open(ids_path, 'r') as f:
                        cached_ids = json.load(f)
                    if cached_ids == self.poem_ids:
                        self.topic_matrix = np.load(matrix_path)
                        self.logger.logger.info(f"成功从缓存加载 {len(self.poem_ids)} 首诗歌的向量矩阵")
                        cache_valid = True
                except Exception as e:
                    self.logger.logger.warning(f"缓存加载失败: {e}")
            
            if not cache_valid:
                # 获取所有诗歌内容重新计算
                contents = [p.content for p in poems]
                self.logger.logger.info(f"正在构建 {len(poems)} 首诗歌的向量矩阵 (全量计算)...")
                self.topic_matrix = batch_get_vectors(contents, self.bertopic_model)
                
                # 保存到缓存
                try:
                    np.save(matrix_path, self.topic_matrix)
                    with open(ids_path, 'w') as f:
                        json.dump(self.poem_ids, f)
                    self.logger.logger.info("向量矩阵已持久化到本地缓存")
                except Exception as e:
                    self.logger.logger.error(f"缓存保存失败: {e}")
            
            self.logger.logger.info("向量矩阵准备就绪")

    def _get_user_profile_vector(self, user_id):
        """构建用户偏好向量 (基于交互历史加权平均)"""
        reviews = Review.query.filter_by(user_id=user_id).all()
        if not reviews or self.topic_matrix is None:
            return None
            
        user_vector = np.zeros(self.topic_matrix.shape[1])
        weight_sum = 0
        
        for r in reviews:
            poem_idx = self.poem_id_map.get(r.poem_id)
            if poem_idx is not None:
                # 简单权重: 1.0 (未来可以引入评分系统)
                w = 1.0
                user_vector += self.topic_matrix[poem_idx] * w
                weight_sum += w
                
        if weight_sum > 0:
            user_vector /= weight_sum
            
        return user_vector

    def _get_similar_users(self, target_user_id, top_k=10):
        """寻找相似用户 (User-CF Strategy)"""
        target_vector = self._get_user_profile_vector(target_user_id)
        if target_vector is None:
            return []
            
        # 获取所有活跃用户的向量
        other_users = User.query.filter(User.id != target_user_id, User.total_reviews > 0).limit(100).all() # 限制计算量
        similarities = []
        
        for u in other_users:
            u_vector = self._get_user_profile_vector(u.id)
            if u_vector is not None:
                sim = cosine_similarity([target_vector], [u_vector])[0][0]
                similarities.append((u.id, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def _topic_based_item_cf(self, user_reviewed_ids, all_poem_indices, top_n=20):
        """基于物品的主题协同过滤"""
        if not user_reviewed_ids or self.topic_matrix is None:
            return []
            
        # 获取用户喜欢的诗歌的向量
        user_reviewed_indices = [self.poem_id_map[pid] for pid in user_reviewed_ids if pid in self.poem_id_map]
        if not user_reviewed_indices:
            return []
            
        reviewed_vectors = self.topic_matrix[user_reviewed_indices]
        
        # 计算所有诗歌与用户历史诗歌的相似度平均值
        # 这里使用矩阵运算加速: (n_all, dim) . (n_reviewed, dim).T -> (n_all, n_reviewed)
        sim_matrix = cosine_similarity(self.topic_matrix, reviewed_vectors)
        # 取平均相似度作为得分
        scores = np.mean(sim_matrix, axis=1)
        
        # 排除已读
        for idx in user_reviewed_indices:
            scores[idx] = -1.0
            
        # 获取Top-N
        top_indices = np.argsort(scores)[::-1][:top_n]
        return [(self.poem_ids[i], float(scores[i])) for i in top_indices if scores[i] > 0]

    def _content_based_recommend(self, target_vector, user_reviewed_indices, top_n=20):
        """基于用户画像向量的内容推荐"""
        if self.topic_matrix is None or target_vector is None:
            return []
            
        # 计算用户向量与所有诗歌的相似度
        scores = cosine_similarity([target_vector], self.topic_matrix)[0]
        
        # 排除已读
        for idx in user_reviewed_indices:
            scores[idx] = -1.0
            
        top_indices = np.argsort(scores)[::-1][:top_n]
        return [(self.poem_ids[i], float(scores[i])) for i in top_indices if scores[i] > 0]

    def get_new_poems_for_user(self, user_id, limit=6):
        """混合推荐主逻辑 (Hybrid Strategy)"""
        user = User.query.get(user_id)
        if not user or not self.bertopic_model:
            return self.get_global_popular(limit)
        
        if self.topic_matrix is None:
            self._build_poem_vector_matrix()
            
        user_reviews = Review.query.filter_by(user_id=user_id).all()
        user_reviewed_ids = {r.poem_id for r in user_reviews}
        user_reviewed_indices = [self.poem_id_map[pid] for pid in user_reviewed_ids if pid in self.poem_id_map]
        
        interaction_count = len(user_reviews)
        candidates = {} # poem_id -> total_score
        
        # 定义动态权重
        if interaction_count == 0:
            # 冷启动用户: 热门为主
            w_cf_user = 0.0
            w_cf_item = 0.0
            w_content = 0.4
            w_popular = 0.6
        elif interaction_count < 10:
            # 轻度用户: 内容+ItemCF为主
            w_cf_user = 0.2
            w_cf_item = 0.4
            w_content = 0.3
            w_popular = 0.1
        else:
            # 重度用户: 协同过滤为主
            w_cf_user = 0.4
            w_cf_item = 0.4
            w_content = 0.2
            w_popular = 0.0
            
        # 1. User-CF Strategy (简化版: 只取相似用户最近喜欢的一首)
        if w_cf_user > 0:
            similar_users = self._get_similar_users(user_id)
            for sim_uid, sim_score in similar_users:
                sim_reviews = Review.query.filter_by(user_id=sim_uid).order_by(Review.created_at.desc()).limit(5).all()
                for r in sim_reviews:
                    if r.poem_id not in user_reviewed_ids:
                        candidates[r.poem_id] = candidates.get(r.poem_id, 0) + (sim_score * w_cf_user)

        # 2. Item-CF Strategy
        if w_cf_item > 0:
            item_recs = self._topic_based_item_cf(user_reviewed_ids, None)
            for pid, score in item_recs:
                candidates[pid] = candidates.get(pid, 0) + (score * w_cf_item)
                
        # 3. Content-Based Strategy
        if w_content > 0:
            user_vec = self._get_user_profile_vector(user_id)
            if user_vec is not None:
                content_recs = self._content_based_recommend(user_vec, user_reviewed_indices)
                for pid, score in content_recs:
                    candidates[pid] = candidates.get(pid, 0) + (score * w_content)
                    
        # 4. Popularity Strategy (Fallback)
        if w_popular > 0 or not candidates:
            popular_poems = self.get_global_popular(limit * 2)
            for p in popular_poems:
                if p.id not in user_reviewed_ids:
                    # 归一化: 热门分 0~1
                    pop_score = min(p.views / 1000.0, 1.0)
                    candidates[p.id] = candidates.get(p.id, 0) + (pop_score * w_popular)
        
        # 排序与返回
        sorted_ids = sorted(candidates.keys(), key=lambda k: candidates[k], reverse=True)
        final_ids = sorted_ids[:limit]
        
        # 兜底
        if len(final_ids) < limit:
            remaining = limit - len(final_ids)
            pops = self.get_global_popular(remaining + 20) # 多取点防重重复
            for p in pops:
                if p.id not in user_reviewed_ids and p.id not in final_ids:
                    final_ids.append(p.id)
                    if len(final_ids) >= limit:
                        break
                        
        # 保持顺序返回对象
        id_map = {p.id: p for p in Poem.query.filter(Poem.id.in_(final_ids)).all()}
        return [id_map[pid] for pid in final_ids if pid in id_map]
    
    def get_global_popular(self, limit=6):
        """获取全局热门诗歌"""
        return Poem.query.order_by(Poem.views.desc()).limit(limit).all()
    
    def batch_update_all_recommendations(self, app=None):
        """全量更新推荐逻辑"""
        flask_app = app or current_app
        with flask_app.app_context():
            # 重建向量矩阵
            self._build_poem_vector_matrix() # 确保最新
            
            # 更新用户偏好缓存 (topics string)
            # 虽然新算法主要用向量实时计算，但为了前端展示，我们还是维护 preference_topics 字段
            users = User.query.all()
            for user in users:
                user.preference_topics = self.update_user_preference(user.id)
                user.total_reviews = Review.query.filter_by(user_id=user.id).count()
            db.session.commit()
            
            # 更新诗歌元数据
            poems = Poem.query.all()
            for poem in poems:
                if not poem.LDA_topic and self.bertopic_model:
                     tid, tname = predict_topic(poem.content, self.bertopic_model)
                     poem.LDA_topic = tname
                     poem.Real_topic = str(tid)
                poem.review_count = Review.query.filter_by(poem_id=poem.id).count()
            db.session.commit()

    def batch_update_recommendations(self, user_ids=None, trigger_type='manual', poem_id=None, app=None):
        """批量更新用户推荐状态"""
        flask_app = app or current_app
        
        with flask_app.app_context():
            if trigger_type == 'new_poem' and poem_id:
                # 如果是新诗插入，为新诗计算 BERTopic 主题
                poem = Poem.query.get(poem_id)
                if poem and self.bertopic_model:
                    tid, tname = predict_topic(poem.content, self.bertopic_model)
                    poem.LDA_topic = tname
                    poem.Real_topic = str(tid)
                    db.session.commit()
                    
                    # 更新向量矩阵缓存 (增量更新暂未实现，简单触发全量重建或append)
                    if self.topic_matrix is not None:
                        # 简单的增量添加
                        vec = get_document_vector(poem.content, self.bertopic_model)
                        if vec is not None:
                            self.topic_matrix = np.vstack([self.topic_matrix, vec])
                            self.poem_ids.append(poem.id)
                            self.poem_id_map[poem.id] = len(self.poem_ids) - 1

            self.batch_update_all_recommendations(flask_app)
            
        return {'success': True, 'processed_users': len(user_ids) if user_ids else 0}


# ==================== 推荐更新服务 ====================

class RecommendationUpdateService:
    """推荐更新服务"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.logger = RecommendationLogger()
        self.recommender = IncrementalRecommender()
        self.pending_update = None
        self.update_lock = threading.Lock()
        self.retry_count = 0
        self.last_update_time = None
        self.new_poem_ids = []  # 待处理的新诗歌ID列表
        self.last_poem_count = 0  # 上次检测的诗歌数量
        self.poll_thread = None  # 后台轮询线程
        self.app = None  # 保存 Flask 应用引用
    
    def register_database_listener(self, app):
        """注册数据库变更监听器 - 使用后台轮询机制"""
        self.app = app  # 保存应用引用
        
        with app.app_context():
            # 获取当前诗歌数量 (容错处理)
            try:
                self.last_poem_count = Poem.query.count()
                self.logger.logger.info(f"🎯 监听器启动，当前诗歌数: {self.last_poem_count}")
            except Exception:
                self.last_poem_count = 0
                self.logger.logger.warning("⚠️ 监听器启动: 数据库表尚不可用，等待初始化")
            
            # 启动后台轮询线程
            self.poll_thread = threading.Thread(
                target=self._poll_for_new_poems,
                args=(app,),
                daemon=True
            )
            self.poll_thread.start()
    
    def _poll_for_new_poems(self, app):
        """轮询检测新诗歌（每10秒检查一次）"""
        while True:
            try:
                time.sleep(10)  # 每10秒检查一次
                
                with app.app_context():
                    current_count = Poem.query.count()
                    
                    if current_count > self.last_poem_count:
                        # 有新诗歌
                        new_count = current_count - self.last_poem_count
                        self.last_poem_count = current_count
                        
                        # 获取最新插入的诗歌ID
                        latest_poem = Poem.query.order_by(Poem.id.desc()).first()
                        if latest_poem:
                            self.logger.logger.info(
                                f"📝 检测到 {new_count} 首新诗歌, 最新ID: {latest_poem.id}"
                            )
                            self._on_new_poem_inserted(latest_poem.id)
                    
            except Exception as e:
                self.logger.logger.error(f"轮询错误: {e}")
                time.sleep(30)  # 错误时等待更长时间
    
    def _on_new_poem_inserted(self, poem_id):
        """新诗歌插入处理"""
        with self.update_lock:
            # 添加到待处理列表
            self.new_poem_ids.append(poem_id)
            
            # 如果已经在等待更新，不再重复添加
            if self.pending_update is not None:
                return
            
            # 设置延迟触发
            self.pending_update = threading.Timer(
                RecommendationConfig.TRIGGER_DELAY,
                self._trigger_update,
                args=(poem_id,)
            )
            self.pending_update.start()
            
            self.logger.logger.info(
                f"📝 检测到新诗歌 (ID: {poem_id}), "
                f"将在 {RecommendationConfig.TRIGGER_DELAY} 秒后触发推荐更新"
            )
    
    def _trigger_update(self, poem_id):
        """触发更新"""
        with self.update_lock:
            self.pending_update = None
            
            # 开始批量更新，传入 app 引用
            result = self.recommender.batch_update_recommendations(
                user_ids=None,
                trigger_type='new_poem',
                poem_id=poem_id,
                app=self.app
            )
            
            # 处理失败重试
            if not result.get('success', False):
                self._handle_retry(poem_id, result)
            else:
                self.retry_count = 0
                self.last_update_time = datetime.now()
                self.new_poem_ids = []  # 清空待处理列表
    
    def _handle_retry(self, poem_id, last_result):
        """处理失败重试"""
        if self.retry_count < RecommendationConfig.MAX_RETRIES:
            self.retry_count += 1
            
            delay = RecommendationConfig.RETRY_DELAY * self.retry_count
            
            self.logger.logger.info(
                f"🔄 计划重试推荐更新 (尝试 {self.retry_count}/{RecommendationConfig.MAX_RETRIES}), "
                f"等待 {delay} 秒"
            )
            
            # 延迟后重试
            timer = threading.Timer(
                delay,
                self._trigger_update,
                args=(poem_id,)
            )
            timer.start()
        else:
            self.logger.log_update_failure(
                f"已达到最大重试次数 ({RecommendationConfig.MAX_RETRIES})",
                retry_count=self.retry_count
            )
            self.retry_count = 0
    
    def manual_trigger_update(self, poem_id=None):
        """手动触发更新"""
        if self.app is None:
            return {'success': False, 'error': 'App not initialized'}
        
        with self.app.app_context():
            user_ids = [u.id for u in User.query.all()]
        
        if not user_ids:
            return {'success': False, 'error': '没有用户'}
        
        result = self.recommender.batch_update_recommendations(
            user_ids,
            trigger_type='manual',
            poem_id=poem_id
        )
        
        if result.get('success', False):
            self.last_update_time = datetime.now()
        
        return result
    
    def get_update_status(self):
        """获取更新状态"""
        return {
            'is_updating': self.pending_update is not None,
            'pending_poems': self.new_poem_ids.copy(),
            'last_update_time': self.last_update_time.isoformat() if self.last_update_time else None,
            'retry_count': self.retry_count,
            'config': {
                'trigger_delay': RecommendationConfig.TRIGGER_DELAY,
                'max_processing_time': RecommendationConfig.MAX_PROCESSING_TIME,
                'cpu_threshold': RecommendationConfig.CPU_THRESHOLD,
                'memory_threshold': RecommendationConfig.MEMORY_THRESHOLD,
                'max_retries': RecommendationConfig.MAX_RETRIES,
                'batch_size': RecommendationConfig.BATCH_SIZE
            }
        }


# ==================== 集成到 Flask 应用 ====================

recommendation_service = None

def init_recommendation_system(app):
    """初始化推荐系统"""
    global recommendation_service
    
    # 创建推荐更新服务
    recommendation_service = RecommendationUpdateService()
    
    # 注册数据库监听器
    recommendation_service.register_database_listener(app)
    
    # 记录初始化完成
    logger = RecommendationLogger()
    logger.logger.info("🎯 推荐更新系统初始化完成")
    logger.logger.info(f"   - 触发延迟: {RecommendationConfig.TRIGGER_DELAY}秒")
    logger.logger.info(f"   - 最大处理时间: {RecommendationConfig.MAX_PROCESSING_TIME}秒")
    logger.logger.info(f"   - CPU阈值: {RecommendationConfig.CPU_THRESHOLD}%")
    logger.logger.info(f"   - 内存阈值: {RecommendationConfig.MEMORY_THRESHOLD}%")
    logger.logger.info(f"   - 最大重试次数: {RecommendationConfig.MAX_RETRIES}")


def add_recommendation_routes(app):
    """添加推荐系统相关的 API 路由"""
    
    @app.route('/api/admin/recommendation/status')
    def get_recommendation_status():
        """获取推荐系统状态"""
        if recommendation_service is None:
            return jsonify({'error': '推荐系统未初始化'}), 500
        
        return jsonify(recommendation_service.get_update_status())
    
    @app.route('/api/admin/recommendation/trigger', methods=['POST'])
    def trigger_recommendation_update():
        """手动触发推荐更新"""
        if recommendation_service is None:
            return jsonify({'error': '推荐系统未初始化'}), 500
        
        data = request.json or {}
        poem_id = data.get('poem_id')
        
        result = recommendation_service.manual_trigger_update(poem_id)
        
        if result.get('success', False):
            return jsonify({
                'message': '推荐更新完成',
                'details': result
            })
        else:
            return jsonify({
                'message': '推荐更新失败',
                'error': result.get('error'),
                'details': result
            }), 500
    
    @app.route('/api/admin/recommendation/logs')
    def get_recommendation_logs():
        """获取推荐更新日志"""
        logger = RecommendationLogger()
        hours = request.args.get('hours', 24, type=int)
        logs = logger.get_recent_logs(hours)
        return jsonify(logs)


# ==================== 单独运行测试 ====================

if __name__ == '__main__':
    print("=" * 60)
    print("自动化推荐更新系统测试")
    print("=" * 60)
    print()
    
    # 模拟测试
    print("1. 测试配置加载...")
    print(f"   触发延迟: {RecommendationConfig.TRIGGER_DELAY}秒")
    print(f"   最大处理时间: {RecommendationConfig.MAX_PROCESSING_TIME}秒")
    print(f"   CPU阈值: {RecommendationConfig.CPU_THRESHOLD}%")
    print(f"   内存阈值: {RecommendationConfig.MEMORY_THRESHOLD}%")
    print(f"   最大重试次数: {RecommendationConfig.MAX_RETRIES}")
    print()
    
    print("2. 测试日志系统...")
    test_logger = RecommendationLogger()
    test_logger.logger.info("测试日志记录")
    print("   ✓ 日志记录成功")
    print()
    
    print("3. 测试性能监控...")
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    time.sleep(0.5)
    cpu, memory = monitor.sample_resources()
    avg_cpu, avg_memory, duration = monitor.get_final_metrics()
    print(f"   CPU使用率: {avg_cpu:.1f}%")
    print(f"   内存使用率: {avg_memory:.1f}%")
    print(f"   监控时长: {duration:.2f}秒")
    print()
    
    print("4. 测试增量推荐计算...")
    recommender = IncrementalRecommender()
    print("   ✓ 推荐计算器初始化成功")
    print()
    
    print("=" * 60)
    print("测试完成！")
    print("=" * 60)
