from flask import Blueprint, request, jsonify, current_app, abort
from .. import db, UPLOAD_FOLDER, allowed_file, skt
from .models import Group, Message
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..auth.models import User
from werkzeug.utils import secure_filename
import os
from flask_socketio import join_room, emit
from flask_socketio import  join_room, leave_room, send
groupsbp = Blueprint('groups', __name__)

@groupsbp.route('/create_group', methods=['POST'])
@jwt_required()
def create_group():
    data = request.get_json()  # Get the JSON data from the request
    group_name = data.get('group_name')  # Access group_name from the JSON data

    if not group_name:
        return jsonify({"error": "Group name is required"}), 400

    # Check if group already exists
    existing_group = Group.query.filter_by(name=group_name).first()
    if existing_group:
        return jsonify({"error": "Group name already exists"}), 409

    group = Group(name=group_name)
    db.session.add(group)
    db.session.commit()
    return jsonify({"message": "Group created", "group_id": group.id}), 201

@groupsbp.route('/join_group/<int:group_id>', methods=['POST'])
@jwt_required()
def join_group(group_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    group = Group.query.get(group_id)

    if not group:
        return jsonify({"error": "Group not found"}), 404

    if user in group.members:
        return jsonify({"message": "Already a member of the group"}), 200

    group.members.append(user)
    db.session.commit()
    return jsonify({"message": "Joined group"}), 200

@groupsbp.route('/delete_group/<int:group_id>', methods=['DELETE'])
@jwt_required()
def delete_group(group_id):
    group = Group.query.get(group_id)

    if not group:
        return jsonify({"error": "Group not found"}), 404

    db.session.delete(group)
    db.session.commit()
    return jsonify({"message": "Group deleted"}), 200

@skt.on('join')
def on_join(data):
    username = data['username']
    group_id = data['group_id']
    join_room(group_id)
    send(f"{username} has entered the room.", to=group_id)

@skt.on('message')
@jwt_required()
def handle_message(data):
    content = data['content']
    group_id = data['group_id']
    user_id = get_jwt_identity()  # Retrieve the current user's ID
    message = Message(content=content, user_id=user_id, group_id=group_id)
    db.session.add(message)
    db.session.commit()
    send(content, to=group_id)

@skt.on('leave')
def on_leave(data):
    username = data['username']
    group_id = data['group_id']
    leave_room(group_id)
    send(f"{username} has left the room.", to=group_id)

@groupsbp.route('/messages/<int:group_id>')
@jwt_required()
def get_messages(group_id):
    messages = Message.query.filter_by(group_id=group_id).order_by(Message.timestamp).all()
    return jsonify([{'user': msg.user_id, 'content': msg.content, 'timestamp': msg.timestamp} for msg in messages])

@groupsbp.route('/my_groups')
@jwt_required()
def my_groups():
    current_user = User.query.get(get_jwt_identity())  # Get the current user from JWT
    groups = current_user.groups
    print(f"Groups for user {current_user.id}: {[group.id for group in groups]}")  # Debugging line
    return jsonify([{'group_id': group.id, 'name': group.name} for group in groups])
