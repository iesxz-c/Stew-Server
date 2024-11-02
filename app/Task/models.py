from datetime import datetime, timedelta
from .. import db

class Task(db.Model):
    _tablename_ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    deadline = db.Column(db.DateTime)
    completed = db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'deadline': self.deadline.isoformat() if self.deadline else None,  # Convert to ISO format
            'completed': self.completed,
            'score': self.score}

    def update_score(self):
        if self.completed:
            if datetime.utcnow() <= self.deadline:
                self.score = 100
            else:
                self.score = -100
        else:
            self.score = 0