from .. import db
from datetime import datetime
from enum import Enum

class FrequencyEnum(Enum):
    DAILY = 'Daily'  # This value should match what you send in the request
    WEEKLY = 'Weekly'
    MONTHLY = 'Monthly'



class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    deadline = db.Column(db.DateTime, nullable=False) 
    frequency = db.Column(db.Enum(FrequencyEnum), nullable=False)  # Enum for better control
    progress = db.Column(db.Float, default=0.0)  # Progress in percentage
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_completed = db.Column(db.Boolean, default=False)

    # No need for this line anymore, since it's already in User model:
    # user = db.relationship('User', backref='goals')

    def __repr__(self):
        return f"<Goal {self.title} (Frequency: {self.frequency.name})>"


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey('goal.id'), nullable=True)  # Optional goal reference
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # No need for this line, as it is already handled by the User model's backref:
    # user = db.relationship('User', backref='notifications')

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

    # Remove the redundant user relationship here
    # user = db.relationship('User', backref='progress')

    def __repr__(self):
        return f"<UserProgress for User {self.user_id}>"


