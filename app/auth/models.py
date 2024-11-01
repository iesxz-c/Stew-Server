from .. import db
#from ..groups.models import Group

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(364), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(100))  # New field for the user's name
    email = db.Column(db.String(150), unique=True)  # New field for the user's email
    profile_picture = db.Column(db.String(250))  # New field for the user's profile picture URL

    # Relationship to access groups the user belongs to
    groups = db.relationship('Group', secondary='group_member')
    goals = db.relationship('Goal', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    progress = db.relationship('UserProgress', backref='user', uselist=False)

