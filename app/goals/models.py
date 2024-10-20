from .. import db
from datetime import datetime

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    deadline = db.Column(db.DateTime, nullable=False) 
    frequency = db.Column(db.String(10), nullable=False)  # Use String instead of Enum
    progress = db.Column(db.Float, default=0.0)  # Progress in percentage
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_completed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Goal {self.title} (Frequency: {self.frequency})>"


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('goal.id'), nullable=True)  # Optional goal reference
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    goal = db.relationship('Goal', backref='notifications')

    def __repr__(self):
        return f"<Notification {self.message}>"
    
class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    daily_progress = db.Column(db.Float, default=0.0)  # Percentage for daily goals
    weekly_progress = db.Column(db.Float, default=0.0)  # Percentage for weekly goals
    monthly_progress = db.Column(db.Float, default=0.0)  # Percentage for monthly goals
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UserProgress for User {self.user_id}>"
