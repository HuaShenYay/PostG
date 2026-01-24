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
    
    # New fields
    total_reviews = db.Column(db.Integer, default=0)
    preference_topics = db.Column(db.Text) # 分析关于该用户的所有评论，得出的具体的主题分布
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'total_reviews': self.total_reviews,
            'preference_topics': self.preference_topics,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def check_password(self, password):
        return self.password_hash == password


class Poem(db.Model):
    __tablename__ = 'poems'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(50))
    content = db.Column(db.Text)
    dynasty = db.Column(db.String(20))
    
    # New metadata fields
    genre_type = db.Column(db.String(50))     # 诗歌类型
    rhythm_name = db.Column(db.String(50))    # 诗歌格律名
    rhythm_type = db.Column(db.String(20))    # 诗歌格律类型
    
    # Stats
    views = db.Column(db.Integer, default=0)
    review_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Recommendation/LDA fields
    LDA_topic = db.Column(db.Text)  # LDA主题名文本
    Real_topic = db.Column(db.Text) # 真实主题（人工标注）
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'content': self.content,
            'dynasty': self.dynasty,
            'genre_type': self.genre_type,
            'rhythm_name': self.rhythm_name,
            'rhythm_type': self.rhythm_type,
            'views': self.views,
            'review_count': self.review_count,
            'LDA_topic': self.LDA_topic,
            'Real_topic': self.Real_topic,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    poem_id = db.Column(db.Integer, db.ForeignKey('poems.id'), nullable=False)
    comment = db.Column(db.Text)
    
    # New fields
    topic_names = db.Column(db.Text) # LDA分析这首评论属于哪个主题名
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    user = db.relationship('User', backref=db.backref('reviews', cascade='all, delete-orphan'))
    poem = db.relationship('Poem', backref=db.backref('reviews', cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'poem_id': self.poem_id,
            'comment': self.comment,
            'topic_names': self.topic_names,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
