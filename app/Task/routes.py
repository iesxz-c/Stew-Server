from flask import Flask, jsonify, request,Blueprint
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from ..import db
from .models import Task
from datetime import datetime, timedelta
taskbp = Blueprint('task',__name__)

@taskbp.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    user_id = get_jwt_identity()
    data = request.get_json()

    try:
        # Attempt to parse the deadline from ISO format
        deadline = datetime.fromisoformat(data['deadline'])
    except ValueError:
        return jsonify({"error": "Invalid date format. Use ISO 8601 format (e.g., YYYY-MM-DDTHH:MM)."}), 400

    task = Task(
        user_id=user_id,
        title=data['title'],
        description=data.get('description', ''),
        deadline=deadline
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({"message": "Task created successfully!"}), 201

@taskbp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    user_id = get_jwt_identity()
    tasks = Task.query.filter_by(user_id=user_id).all()
    return jsonify([task.to_dict() for task in tasks]), 200

@taskbp.route('/tasks/<int:task_id>/complete', methods=['POST'])
@jwt_required()
def complete_task(task_id):
    user_id = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()
    task.completed = True
    task.update_score()
    db.session.commit()
    return jsonify({"message": "Task marked as completed!"}), 200

@taskbp.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    user_id = get_jwt_identity()
    task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted successfully!"}), 200

@taskbp.route('/tasks/scores', methods=['GET'])
@jwt_required()
def get_scores():
    user_id = get_jwt_identity()  # Get the identity of the current user
    tasks = Task.query.filter_by(user_id=user_id).all()  # Fetch tasks for the current user
    total_tasks = len(tasks)  # Count total tasks
    total_completed = sum(1 for task in tasks if task.completed)  # Count completed tasks
    total_score = sum(task.score for task in tasks if task.completed)  # Sum scores of completed tasks

    return jsonify({
        'total_tasks': total_tasks,          # Return total tasks
        'total_completed': total_completed,  # Return completed tasks
        'total_score': total_score           # Return total score of completed tasks
    })
