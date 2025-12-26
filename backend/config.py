from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 数据库配置类
class Config:
    # 格式: mysql+pymysql://用户名:密码@地址:端口/数据库名
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost/poetry_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 让json响应支持中文
    JSON_AS_ASCII = False

