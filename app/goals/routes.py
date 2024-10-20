from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import Goal, Notification, UserProgress
from .. import db, skt
from datetime import datetime, timedelta

goalsbp = Blueprint('goals', __name__)

@goalsbp.route('/goals', methods=['POST'])
@jwt_required()
def create_goal():
    user_id = get_jwt_identity()
    data = request.get_json()

    title = data.get('title')
    description = data.get('description')
    frequency = data.get('frequency') # Convert to capitalized form
    deadline_str = data.get('deadline')

    # Convert the deadline string to a datetime object
    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%dT%H:%M:%S")  # Specify the expected format
    except ValueError:
        return jsonify({"message": "Invalid deadline format"}), 400

    # Ensure the frequency is valid
    if frequency not in ['Daily', 'Weekly', 'Monthly']:
        return jsonify({"message": "Invalid frequency"}), 400

    goal = Goal(
        title=title, 
        description=description, 
        frequency=frequency,  # Store the capitalized frequency
        deadline=deadline,  # Use the converted datetime object
        user_id=user_id
    )

    db.session.add(goal)
    db.session.commit()

    # Recalculate progress after goal creation
    progress_percentage = calculate_progress(user_id, frequency)
    update_user_progress(user_id, frequency, progress_percentage)

    # Emit a real-time notification to the user
    skt.emit('notification', {
        'message': f"New goal created: {title}",
        'goal_id': goal.id
    }, room=user_id)

    return jsonify({"message": "Goal created", "progress": progress_percentage}), 201

# Route to complete a goal
@goalsbp.route('/goals/<int:goal_id>/complete', methods=['POST'])
@jwt_required()
def complete_goal(goal_id):
    user_id = get_jwt_identity()
    print("User ID from token:", user_id) 
    goal = Goal.query.get_or_404(goal_id)
    print("User ID from token:", goal.user_id) 


    if goal.user_id != user_id:
        return jsonify({"message": "Unauthorized"}), 403

    goal.is_completed = True
    db.session.commit()

    # Recalculate and update progress
    progress_percentage = calculate_progress(user_id, goal.frequency)
    update_user_progress(user_id, goal.frequency, progress_percentage)

    # Emit a real-time notification about the completion
    skt.emit('notification', {
        'message': f"Goal completed: {goal.title}",
        'goal_id': goal.id
    }, room=user_id)

    return jsonify({
        "message": "Goal marked as completed",
        "progress": progress_percentage
    }), 200

# Route to get user's progress
@goalsbp.route('/progress', methods=['GET'])
@jwt_required()
def get_progress():
    user_id = get_jwt_identity()
    progress = UserProgress.query.filter_by(user_id=user_id).first()

    if not progress:
        return jsonify({"message": "No progress data found"}), 404

    return jsonify({
        "daily_progress": progress.daily_progress,
        "weekly_progress": progress.weekly_progress,
        "monthly_progress": progress.monthly_progress,
        "last_updated": progress.last_updated.strftime('%Y-%m-%d %H:%M:%S')
    }), 200

# Route to update user progress
@goalsbp.route('/progress/update', methods=['POST'])
@jwt_required()
def update_progress():
    user_id = get_jwt_identity()
    data = request.get_json()
    frequency = data.get('frequency')  # Can be 'daily', 'weekly', or 'monthly'
    new_progress = data.get('progress')

    if frequency not in ['daily', 'weekly', 'monthly']:
        return jsonify({"message": "Invalid frequency"}), 400

    progress = UserProgress.query.filter_by(user_id=user_id).first()

    if not progress:
        progress = UserProgress(user_id=user_id)

    # Update the appropriate progress field
    if frequency == 'daily':
        progress.daily_progress = new_progress
    elif frequency == 'weekly':
        progress.weekly_progress = new_progress
    elif frequency == 'monthly':
        progress.monthly_progress = new_progress

    progress.last_updated = datetime.utcnow()
    db.session.add(progress)
    db.session.commit()

    return jsonify({"message": "Progress updated successfully"}), 200

def update_user_progress(user_id, frequency, progress_percentage):
    progress = UserProgress.query.filter_by(user_id=user_id).first()

    if not progress:
        progress = UserProgress(user_id=user_id)

    # Update the appropriate progress field
    if frequency == 'daily':
        progress.daily_progress = progress_percentage
    elif frequency == 'weekly':
        progress.weekly_progress = progress_percentage
    elif frequency == 'monthly':
        progress.monthly_progress = progress_percentage

    progress.last_updated = datetime.utcnow()
    db.session.add(progress)
    db.session.commit()

def calculate_progress(user_id, frequency):
    now = datetime.utcnow()
    goals = []  # Initialize an empty list for goals in case of invalid frequency

    if frequency == 'daily':
        start_of_day = datetime(now.year, now.month, now.day)
        end_of_day = start_of_day + timedelta(days=1)
        goals = Goal.query.filter(Goal.user_id == user_id, Goal.deadline >= start_of_day, Goal.deadline < end_of_day).all()

    elif frequency == 'weekly':
        start_of_week = now - timedelta(days=now.weekday())  # Start of the week (Monday)
        end_of_week = start_of_week + timedelta(days=7)
        goals = Goal.query.filter(Goal.user_id == user_id, Goal.deadline >= start_of_week, Goal.deadline < end_of_week).all()

    elif frequency == 'monthly':
        start_of_month = datetime(now.year, now.month, 1)
        next_month = (now.month % 12) + 1
        start_of_next_month = datetime(now.year if next_month > 1 else now.year + 1, next_month, 1)
        goals = Goal.query.filter(Goal.user_id == user_id, Goal.deadline >= start_of_month, Goal.deadline < start_of_next_month).all()

    else:
        # Handle invalid frequency by returning 0 progress or raise an error
        return 0

    total_goals = len(goals)
    if total_goals == 0:
        return 0  # Return 0 if no goals exist for the period

    completed_goals = sum(1 for goal in goals if goal.is_completed)
    progress_percentage = (completed_goals / total_goals * 100)

    return progress_percentage

@goalsbp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    notifications = Notification.query.filter_by(user_id=user_id, is_read=False).all()

    return jsonify([{
        'id': notification.id,
        'message': notification.message,
        'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for notification in notifications]), 200

@goalsbp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_as_read(notification_id):
    user_id = get_jwt_identity()
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first_or_404()

    notification.is_read = True
    db.session.commit()

    return jsonify({"message": "Notification marked as read"}), 200
