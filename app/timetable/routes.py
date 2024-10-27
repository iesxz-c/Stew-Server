from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from .models import Timetable
from datetime import datetime

timetable_bp = Blueprint('timetable', __name__)

@timetable_bp.route('/create', methods=['POST'])
@jwt_required()
def create_timetable():
    user_id = get_jwt_identity()
    data = request.get_json()

    new_entry = Timetable(
        user_id=user_id,
        title=data['title'],
        description=data.get('description'),
        start_time=datetime.fromisoformat(data['start_time']),
        end_time=datetime.fromisoformat(data['end_time']),
        color=data.get('color')
    )
    
    try:
        db.session.add(new_entry)
        db.session.commit()
        return jsonify({"message": "Timetable entry created successfully!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to create entry"}), 500


@timetable_bp.route('/edit/<int:id>', methods=['PUT'])
@jwt_required()
def edit_timetable(id):
    user_id = get_jwt_identity()
    data = request.get_json()
    entry = Timetable.query.filter_by(id=id, user_id=user_id).first()

    if not entry:
        return jsonify({"message": "Entry not found"}), 404

    entry.title = data.get('title', entry.title)
    entry.description = data.get('description', entry.description)
    entry.start_time = datetime.fromisoformat(data.get('start_time', entry.start_time.isoformat()))
    entry.end_time = datetime.fromisoformat(data.get('end_time', entry.end_time.isoformat()))
    entry.color = data.get('color', entry.color)
    
    try:
        db.session.commit()
        return jsonify({"message": "Entry updated successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to update entry"}), 500


@timetable_bp.route('/delete/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_timetable(id):
    user_id = get_jwt_identity()
    entry = Timetable.query.filter_by(id=id, user_id=user_id).first()

    if not entry:
        return jsonify({"message": "Entry not found"}), 404

    try:
        db.session.delete(entry)
        db.session.commit()
        return jsonify({"message": "Entry deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Failed to delete entry"}), 500


@timetable_bp.route('/list', methods=['GET'])
@jwt_required()
def list_timetables():
    user_id = get_jwt_identity()
    entries = Timetable.query.filter_by(user_id=user_id).all()
    data = [
        {
            "id": entry.id,
            "title": entry.title,
            "description": entry.description,
            "start_time": entry.start_time.isoformat(),
            "end_time": entry.end_time.isoformat(),
            "color": entry.color
        }
        for entry in entries
    ]
    return jsonify(data), 200
