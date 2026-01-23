from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# 这里的 db 稍后会在 app.py 里 init_app
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), default='123456')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 新增：持久化用户的偏好主题（JSON字符串或格式化文本）
    # 存储形如：[{"topic_id": 1, "score": 0.8}, ...]
    preference_topics = db.Column(db.Text) 
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'preference_topics': self.preference_topics
        }
    
    def check_password(self, password):
        return self.password_hash == password


class Poem(db.Model):
    __tablename__ = 'poems'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(50))
    content = db.Column(db.Text)
    
    # Enhanced Fields for Real Data
    dynasty = db.Column(db.String(20), default='Tang')
    translation = db.Column(db.Text)  # Modern Chinese Translation
    appreciation = db.Column(db.Text) # Shangxi
    author_bio = db.Column(db.Text)   # Author Biography
    notes = db.Column(db.Text)        # JSON string for Allusions/Notes
    
    # Rhythm Fields
    rhythm_name = db.Column(db.String(50))   # e.g. "Dian Jiang Chun"
    rhythm_type = db.Column(db.String(20))   # e.g. "Ci", "Shi"
    tonal_summary = db.Column(db.Text)       # JSON string for tonal analysis metrics
    
    # Global Analysis Fields
    likes = db.Column(db.Integer, default=0)  # 点赞数
    views = db.Column(db.Integer, default=0)  # 浏览数
    shares = db.Column(db.Integer, default=0)  # 分享数
    tags = db.Column(db.Text)  # JSON string for tags
    difficulty_level = db.Column(db.String(10), default='medium')  # 难度等级
    theme_category = db.Column(db.String(50))  # 主题分类
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'content': self.content,
            'dynasty': self.dynasty,
            'translation': self.translation,
            'appreciation': self.appreciation,
            'author_bio': self.author_bio,
            'rhythm_name': self.rhythm_name,
            'rhythm_type': self.rhythm_type,
            'tonal_summary': self.tonal_summary,
            'likes': self.likes,
            'views': self.views,
            'shares': self.shares,
            'tags': self.tags,
            'difficulty_level': self.difficulty_level,
            'theme_category': self.theme_category,
            'created_at': self.created_at.isoformat() if self.created_at else None
            # notes are fetched separately usually, but good to have access
        }

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    poem_id = db.Column(db.Integer, db.ForeignKey('poems.id'), nullable=False)
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    
    # 新增：存储该条评论的主题分布情况
    # 存储形如：{"0": 0.1, "1": 0.9} 之类的 JSON
    topic_distribution = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 建立关联关系
    user = db.relationship('User', backref='reviews')
    poem = db.relationship('Poem', backref='reviews')
