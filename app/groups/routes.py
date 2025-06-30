from flask import Blueprint, request, jsonify,current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity, decode_token
from .. import db, skt,allowed_file,UPLOAD_FOLDER
import os
from ..auth.models import User
from .models import Group, Message,GroupMember
from flask_socketio import join_room, leave_room, send
from flask_jwt_extended.exceptions import NoAuthorizationError,InvalidHeaderError

groupsbp = Blueprint('groups', __name__)

@groupsbp.route('/create_group', methods=['POST'])
@jwt_required()
def create_group():
    data = request.get_json()
    group_name = data.get('group_name')
    owner_id = get_jwt_identity()

    if not group_name:
        return jsonify({"error": "Group name is required"}), 400

    existing_group = Group.query.filter_by(name=group_name).first()
    if existing_group:
        return jsonify({"error": "Group name already exists"}), 409

    group = Group(name=group_name, owner_id=owner_id)
    db.session.add(group)
    db.session.commit()

    group.members.append(User.query.get(owner_id))
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
    user_id = get_jwt_identity()

    if not group:
        return jsonify({"error": "Group not found"}), 404

    if group.owner_id != user_id:
        return jsonify({"error": "Only the owner can delete this group"}), 403
    
    Message.query.filter_by(group_id=group.id).delete()

    # Delete associated members
    GroupMember.query.filter_by(group_id=group.id).delete()
    db.session.delete(group)
    db.session.commit()
    return jsonify({"message": "Group deleted"}), 200

@groupsbp.route('/all_groups', methods=['GET'])
@jwt_required()
def all_groups():
    groups = Group.query.all()
    return jsonify([{'group_id': group.id, 'name': group.name, 'owner_id': group.owner_id} for group in groups])

def verify_token(data):
    token = data.get('token')
    if not token:
        raise NoAuthorizationError("Missing Authorization Token")

    try:
        jwt_data = decode_token(token)
        return jwt_data['sub']  # Assuming 'sub' is the user ID
    except InvalidHeaderError:
        raise NoAuthorizationError("Invalid or expired token")

@skt.on('join')
def on_join(data):
    try:
        user_id = verify_token(data['auth'])
        username = data['username']
        group_id = data['group_id']

        join_room(group_id)
        send({"type":"notification","content":f"{username} is in the Chat"}, to=group_id)
    except NoAuthorizationError as e:
        send(str(e), to=request.sid)

@skt.on('message')
def handle_message(data):
    try:
        user_id = verify_token(data['auth'])
        content = data['content']
        group_id = data['group_id']
        user = User.query.get(user_id)
        message = Message(content=content, user_id=user_id, group_id=group_id)
        db.session.add(message)
        db.session.commit()
        send({'sender':user.username,'content':content}, to=group_id)
    except NoAuthorizationError as e:
        send(str(e), to=request.sid)

@skt.on('leave')
def on_leave(data):
    try:
        user_id = verify_token(data['auth'])
        username = data['username']
        group_id = data['group_id']

        leave_room(group_id)
        send({"type":"notification","content": f"{username} went offline."}, to=group_id)
    except NoAuthorizationError as e:
        send(str(e), to=request.sid)

@groupsbp.route('/upload/<int:group_id>', methods=['POST'])
@jwt_required()
def upload_file(group_id):
    user_id = get_jwt_identity()

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        group_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], f"group_{group_id}")
        os.makedirs(group_folder, exist_ok=True)  # ✅ Create per-group folder if not exist

        file_path = os.path.join(group_folder, filename)
        file.save(file_path)

        return jsonify({
            "message": "File uploaded",
            "file_url": f"/uploads/group/{group_id}/{filename}"
        }), 201

    return jsonify({"error": "File type not allowed"}), 400

@groupsbp.route('/group_files/<int:group_id>', methods=['GET'])
@jwt_required()
def list_group_files(group_id):
    group_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], f"group_{group_id}")
    if not os.path.exists(group_folder):
        return jsonify([])

    files = os.listdir(group_folder)
    file_urls = [f"/uploads/group_{group_id}/{f}" for f in files]
    return jsonify(file_urls) 