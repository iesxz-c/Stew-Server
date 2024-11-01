from .. import db
from ..auth.models import User
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    members = db.relationship('User', secondary='group_member')
    messages = db.relationship('Message', backref='group', lazy=True)

class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)


#       __tablename__ = 'file'
 #     id = db.Column(db.Integer, primary_key=True)
 #     group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
  #    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  #    filename = db.Column(db.String(255), nullable=False)
   #   timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

   #   user = db.relationship('User')
   #   group = db.relationship('Group')
