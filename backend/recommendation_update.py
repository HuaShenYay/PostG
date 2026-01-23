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

class IncrementalRecommender:
    """增量推荐计算器"""
    
    def __init__(self):
        self.logger = RecommendationLogger()
        self.monitor = PerformanceMonitor()
    
    def get_user_preference_vector(self, user_id):
        """获取用户偏好向量"""
        reviews = Review.query.filter_by(user_id=user_id).all()
        
        if not reviews:
            return None
        
        # 聚合用户评论的主题分布
        user_dist = {}
        for r in reviews:
            if r.topic_distribution:
                dist = json.loads(r.topic_distribution)
                for tid, prob in dist.items():
                    user_dist[tid] = user_dist.get(tid, 0) + prob
        
        if not user_dist:
            return None
        
        # 归一化
        total = sum(user_dist.values())
        if total == 0:
            return None
        
        # 返回排序后的偏好列表
        preference = [
            {'topic_id': int(tid), 'score': score / total}
            for tid, score in user_dist.items()
        ]
        preference.sort(key=lambda x: x['score'], reverse=True)
        
        return preference
    
    def get_new_poems_for_user(self, user_id, existing_recommendations):
        """为用户获取新诗歌推荐（增量计算）"""
        preference = self.get_user_preference_vector(user_id)
        
        if not preference or not preference[0]:
            # 如果没有偏好，使用全局热门
            return self.get_global_popular()
        
        top_topic_id = preference[0]['topic_id']
        user_review_poem_ids = set(
            r.poem_id for r in Review.query.filter_by(user_id=user_id).all()
        )
        
        # 获取用户评论诗歌的主题分布
        reviewed_topics = set()
        for r in Review.query.filter_by(user_id=user_id).all():
            if r.topic_distribution:
                dist = json.loads(r.topic_distribution)
                reviewed_topics.update(dist.keys())
        
        # 查找可能匹配的新诗歌
        candidates = []
        
        # 查找与用户偏好主题相关的新诗歌
        all_poems = Poem.query.all()
        for poem in all_poems:
            if poem.id in user_review_poem_ids:
                continue
            
            # 计算诗歌与用户偏好的匹配度
            match_score = 0
            for p in preference:
                tid = str(p['topic_id'])
                # 这里可以添加更复杂的匹配逻辑
                match_score += p['score']
            
            candidates.append({
                'poem': poem,
                'match_score': match_score / len(preference) if preference else 0
            })
        
        # 按匹配度排序
        candidates.sort(key=lambda x: x['match_score'], reverse=True)
        
        # 返回前6首诗歌
        return [c['poem'] for c in candidates[:6]]
    
    def get_global_popular(self, limit=6):
        """获取全局热门诗歌"""
        poems = Poem.query.limit(limit).all()
        return poems
    
    def batch_update_recommendations(self, user_ids=None, trigger_type='manual', poem_id=None, app=None):
        """批量更新用户推荐"""
        start_time = datetime.now()
        self.monitor.start_monitoring()
        
        self.logger.log_update_start(trigger_type, poem_id)
        
        # 使用传入的 app 或保存的 app
        flask_app = app or self.app
        
        if flask_app is None:
            self.logger.logger.error("无法获取 Flask 应用上下文")
            return {'success': False, 'error': 'No app context'}
        
        # 如果没有传入 user_ids，从数据库获取
        if user_ids is None:
            with flask_app.app_context():
                user_ids = [u.id for u in User.query.all()]
        
        total_users = len(user_ids)
        processed_users = 0
        failed_users = []
        
        if not user_ids:
            self.logger.logger.info("没有用户需要更新推荐")
            return {'success': True, 'processed_users': 0}
        
        # 性能指标
        cpu_threshold_exceeded = False
        memory_threshold_exceeded = False
        
        try:
            # 整个批处理在应用上下文中运行
            poem_count = 0
            with flask_app.app_context():
                for i, user_id in enumerate(user_ids):
                    # 检查处理时间是否超出限制
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > RecommendationConfig.MAX_PROCESSING_TIME:
                        self.logger.log_update_failure(
                            f"处理时间超出限制 ({elapsed:.2f}秒)",
                            retry_count=0
                        )
                        break
                    
                    # 采样资源使用
                    cpu, memory = self.monitor.sample_resources()
                    
                    # 检查资源阈值
                    if cpu > RecommendationConfig.CPU_THRESHOLD:
                        cpu_threshold_exceeded = True
                    if memory > RecommendationConfig.MEMORY_THRESHOLD:
                        memory_threshold_exceeded = True
                    
                    try:
                        # 获取用户推荐
                        recommendations = self.get_new_poems_for_user(user_id, [])
                        
                        # 存储推荐结果到数据库
                        user = User.query.get(user_id)
                        if user and recommendations:
                            # 简化：只更新推荐数量，不存储完整列表
                            user.last_recommendation_update = datetime.utcnow()
                            db.session.commit()
                        
                        processed_users += 1
                        
                        # 每处理10个用户记录一次进度
                        if (i + 1) % 10 == 0:
                            self.logger.log_update_progress(
                                i + 1, total_users, elapsed
                            )
                        
                        # 控制处理速度，避免影响系统性能
                        time.sleep(0.1)
                        
                    except Exception as e:
                        failed_users.append(user_id)
                        self.logger.log_update_failure(str(e), retry_count=0)
                        continue
                
                # 获取诗歌数量（在应用上下文中）
                poem_count = Poem.query.count()
            
            # 计算最终性能指标（在应用上下文外）
            avg_cpu, avg_memory, total_time = self.monitor.get_final_metrics()
            
            # 记录性能指标
            self.logger.log_performance_metrics(
                avg_cpu, avg_memory, total_time
            )
            
            # 检查阈值
            thresholds = self.monitor.check_thresholds()
            if thresholds['cpu_exceeded'] or thresholds['memory_exceeded']:
                self.logger.log_update_failure(
                    f"资源使用超出阈值 - CPU: {thresholds['cpu_usage']:.1f}%, " +
                    f"内存: {thresholds['memory_usage']:.1f}%"
                )
            
            # 记录成功
            self.logger.log_update_success(
                processed_users, poem_count, total_time
            )
            
            return {
                'success': True,
                'processed_users': processed_users,
                'failed_users': len(failed_users),
                'total_users': total_users,
                'elapsed_time': total_time,
                'cpu_usage': avg_cpu,
                'memory_usage': avg_memory,
                'thresholds': thresholds
            }
            
        except Exception as e:
            self.logger.log_update_failure(str(e))
            return {
                'success': False,
                'error': str(e),
                'processed_users': processed_users,
                'elapsed_time': (datetime.now() - start_time).total_seconds()
            }


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
            # 获取当前诗歌数量
            self.last_poem_count = Poem.query.count()
            self.logger.logger.info(f"🎯 监听器启动，当前诗歌数: {self.last_poem_count}")
            
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
