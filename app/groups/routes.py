from flask import Blueprint, request, jsonify, current_app, abort
from .. import db, UPLOAD_FOLDER, allowed_file, skt
from .models import Group, Message, File,GroupMembers
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..auth.models import User
from werkzeug.utils import secure_filename
import os
from flask_socketio import join_room, emit

groupsbp = Blueprint('groups', __name__)

@groupsbp.route("/groups", methods=['POST'])
@jwt_required()
def create_group():
    data = request.get_json()
    groupname = data.get('name')

    if Group.query.filter_by(name=groupname).first():
        return jsonify({"message": "Group already exists"}), 400

    group = Group(name=groupname)

    try:
        db.session.add(group)
        db.session.commit()
        
        user_id = get_jwt_identity()
        return jsonify({"message": "Group created", "group_id": group.id, "user_id": user_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating group", "error": str(e)}), 500

@groupsbp.route("/groups/list", methods=['GET'])
@jwt_required()
def get_groups():
    groups = Group.query.all()
    return jsonify([{'id': group.id, 'name': group.name} for group in groups]), 200

@groupsbp.route("/groups/join", methods=['POST'])
@jwt_required()
def join_group():
    data = request.get_json()
    groupname = data.get('name')
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)

    try:
        group = Group.query.filter_by(name=groupname).first()

        if group:
            if user not in group.members:
                group.members.append(user)
                db.session.commit()
                return jsonify({"message": "User joined group", "group_id": group.id, "user_id": user.id}), 200
            else:
                return jsonify({"message": "User already in group"}), 400
        else:
            return jsonify({"message": "Group does not exist"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error joining group", "error": str(e)}), 500

@groupsbp.route('/groups/<int:group_id>/members', methods=['POST'])
@jwt_required()
def add_member(group_id):
    data = request.get_json()
    user_id = data.get('user_id')
    group = Group.query.get_or_404(group_id)
    user = User.query.get_or_404(user_id)

    if user in group.members:
        return jsonify({"message": "User already in group"}), 400

    group.members.append(user)
    try:
        db.session.commit()
        return jsonify({"message": "User added to group", "group_id": group.id, "user_id": user.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error adding user to group", "error": str(e)}), 500

@groupsbp.route('/groups/<int:group_id>/messages', methods=['POST'])
@jwt_required()
def send_message(group_id):
    data = request.get_json()
    content = data.get('content')
    user_id = get_jwt_identity()

    message = Message(content=content, user_id=user_id, group_id=group_id)

    try:
        db.session.add(message)
        db.session.commit()

        skt.emit('receive_message', {
            'id': message.id,
            'content': message.content,
            'username': message.user.username,
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }, room=group_id)

        return jsonify({"message": "Message sent"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error sending message", "error": str(e)}), 500

@groupsbp.route('/groups/<int:group_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(group_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    messages_query = Message.query.filter_by(group_id=group_id).order_by(Message.timestamp.asc())
    messages = messages_query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'messages': [{
            'id': message.id,
            'content': message.content,
            'username': message.user.username,
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } for message in messages.items],
        'total': messages.total,
        'pages': messages.pages,
        'current_page': messages.page,
        'has_next': messages.has_next,
        'has_prev': messages.has_prev
    }), 200

@groupsbp.route('/groups/<int:group_id>/upload', methods=['POST'])
@jwt_required()
def upload_file(group_id):
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
            os.makedirs(current_app.config['UPLOAD_FOLDER'])

        try:
            file.save(file_path)

            new_file = File(group_id=group_id, user_id=get_jwt_identity(), filename=filename)
            db.session.add(new_file)
            db.session.commit()

            skt.emit('file_uploaded', {
                'user_id': get_jwt_identity(),
                'filename': filename,
                'group_id': group_id
            }, room=group_id)

            return jsonify({'message': 'File uploaded successfully!', 'filename': filename}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': 'An error occurred while uploading the file', 'error': str(e)}), 500

    return jsonify({'message': 'File type not allowed'}), 400

@skt.on('send_message')
def handle_send_message(data):
    user_id = data.get('user_id')  # Use .get() to avoid KeyError
    content = data.get('content')
    group_id = data.get('group_id')

    # Check if user_id is None
    if user_id is None:
        print("Received user_id is None")
        return  # or handle the error as needed

    # Insert the message into the database
    new_message = Message(content=content, group_id=group_id, user_id=user_id)
    db.session.add(new_message)
    db.session.commit()

    # Optionally emit back the message to the group
    skt.emit('receive_message', {'content': content, 'user_id': user_id}, room=group_id)
 

@skt.on('join_group')
def on_join(data):
    group_id = data['group_id']
    user_id = data['user_id']
    join_room(group_id)
    emit('user_joined', {'user_id': user_id, 'group_id': group_id}, room=group_id)

@skt.on('upload_file')
def handle_upload_file(data):
    group_id = data['group_id']
    user_id = data['user_id']
    filename = data['filename']
    
    new_file = File(group_id=group_id, user_id=user_id, filename=filename)
    db.session.add(new_file)
    db.session.commit()
    
    emit('file_uploaded', {'user_id': user_id, 'filename': filename}, broadcast=True)

@groupsbp.route('/groups/<int:group_id>/leave', methods=['POST'])
@jwt_required()
def leave_group(group_id):
    user_id = get_jwt_identity()
    group = Group.query.get_or_404(group_id)
    user = User.query.get_or_404(user_id)

    if user in group.members:
        group.members.remove(user)
        db.session.commit()

        skt.emit('user_left', {'user_id': user.id, 'group_id': group_id}, room=group_id)
        return jsonify({"message": "User left the group"}), 200
    else:
        return jsonify({"message": "User is not in this group"}), 400


@groupsbp.route('/groups/<int:group_id>', methods=['DELETE'])
@jwt_required()
def delete_group(group_id):
    group = Group.query.get_or_404(group_id)

    try:
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)

        # Check if the user is a member or the owner of the group if necessary
        # for example, remove this if you don’t need that check

        # Manually delete associated group members
        GroupMembers.query.filter_by(group_id=group_id).delete()

        db.session.delete(group)
        db.session.commit()
        
        return jsonify({"message": "Group deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error deleting group", "error": str(e)}), 500
