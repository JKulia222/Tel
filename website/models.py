from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150))
    registration_date = db.Column(db.DateTime(timezone=True), default=func.now())
    password = db.Column(db.String(150), nullable=False)
    notes = db.relationship('Note', backref='author')


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creation_date = db.Column(db.DateTime(timezone=True), default=func.now())
    modification_date = db.Column(db.DateTime(timezone=True))
    is_public = db.Column(db.Boolean, nullable=False, default=False)
