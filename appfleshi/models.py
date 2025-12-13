from flask_login import UserMixin
from appfleshi import database, login_manager
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(database.Model, UserMixin):
    id = database.Column(database.Integer, primary_key=True)
    username = database.Column(database.String(20), unique=True, nullable=False)
    email = database.Column(database.String(100), unique=True, nullable=False)
    password = database.Column(database.String(60), nullable=False)
    photos = database.relationship('Photo', backref='user', lazy='select')
    comments = database.relationship('Comment', backref='user', lazy='select')
    likes = database.relationship('Like', backref='user', lazy='select')

class Photo(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    file_name = database.Column(database.String(255), nullable=False)
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)
    timestamp = database.Column(database.DateTime, default=datetime.utcnow)
    comments = database.relationship('Comment', backref='photo', lazy='dynamic')
    likes = database.relationship('Like', backref='photo', lazy='dynamic')

class Like(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)
    photo_id = database.Column(database.Integer, database.ForeignKey('photo.id'), nullable=False)

class Comment(database.Model):
    id = database.Column(database.Integer, primary_key=True)
    content = database.Column(database.String(500), nullable=False)
    timestamp = database.Column(database.DateTime, default=datetime.utcnow)
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'), nullable=False)
    photo_id = database.Column(database.Integer, database.ForeignKey('photo.id'), nullable=False)