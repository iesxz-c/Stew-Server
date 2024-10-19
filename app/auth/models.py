from .. import db
from ..groups.models import Group

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(364), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    # Relationship to access groups the user belongs to
    groups = db.relationship('Group', secondary='group_members', backref='user_groups')
    goals = db.relationship('Goal', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    progress = db.relationship('UserProgress', backref='user', uselist=False)
