from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# 这里的 db 稍后会在 app.py 里 init_app
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), default='123456')  # 简单起见，默认密码123456
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username
        }
    
    def check_password(self, password):
        # 简单比对，生产环境应使用 werkzeug.security 的 hash
        return self.password_hash == password


class Poem(db.Model):
    __tablename__ = 'poems'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(50))
    # TEXT类型可以存储长文本
    content = db.Column(db.Text)
    
    def to_dict(self):
        """转为字典，方便API返回JSON"""
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'content': self.content
        }

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    poem_id = db.Column(db.Integer, db.ForeignKey('poems.id'), nullable=False)
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    
    # 建立关联关系
    user = db.relationship('User', backref='reviews')
    poem = db.relationship('Poem', backref='reviews')
