from flask import Blueprint, request, jsonify,current_app
from .. import db,allowed_file,UPLOAD_FOLDER
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import os
from werkzeug.utils import secure_filename
import logging
from flask import send_from_directory
authbp = Blueprint('auth', __name__)


@authbp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@authbp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "User already exists"}), 400
    
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    
    new_user = User(username=data['username'], password=hashed_password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while registering the user"}), 500

    
@authbp.route('/login',methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password,data['password']):
        return jsonify({'message':'Invalid Learner Details'})
    token = create_access_token(identity=user.id)
    return jsonify({'token':token}),200

@authbp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    userid = get_jwt_identity()
    user = User.query.filter_by(id=userid).first()
    
    if not user:
        return jsonify({"message": "User not found"}), 404  # Handle case where user does not exist
    
    return jsonify({
        'username': user.username,
        'email': user.email,  # Include email
        'name': user.name,    # Include name
        'profile_picture': user.profile_picture  
    }), 200



@authbp.route('/change_password', methods=['PUT'])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()  # Get the user ID from the token
    user = User.query.get(user_id)  # Fetch the current user

    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()  # Use JSON for request body
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    # Check if the old password is correct
    if not check_password_hash(user.password, old_password):
        return jsonify({"message": "Old password is incorrect"}), 400

    # Update the user's password
    user.password = generate_password_hash(new_password, method='pbkdf2:sha256')

    try:
        db.session.commit()  # Commit changes to the database
        return jsonify({"message": "Password updated successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while updating the password"}), 500

@authbp.route('/edit_profile', methods=['PUT'])
@jwt_required()
def edit_profile():
    user_id = get_jwt_identity()  # Get the user ID from the token
    user = User.query.get(user_id)  # Fetch the current user

    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.form  # Use request.form for form data
    # Handle file upload
    file = request.files.get('profile_picture')

    # Check if a profile picture file is included in the request
    if file and allowed_file(file.filename):  # Ensure the file type is allowed
        # Delete the old profile picture if it exists
        if user.profile_picture:
            old_picture_path = os.path.join(current_app.config['UPLOAD_FOLDER'], user.profile_picture)
            if os.path.isfile(old_picture_path):  # Check if the file exists
                try:
                    os.remove(old_picture_path)  # Delete the old profile picture file
                except OSError as e:
                    logging.error(f"Error deleting file: {e}")

        # Save the new profile picture
        filename = secure_filename(file.filename)  # Sanitize the filename
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Update user's profile picture path
        user.profile_picture = filename  # Save just the filename for the database

    # Update user's other fields if provided
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        user.email = data['email']
    if 'username' in data:
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user and existing_user.id != user.id:
            return jsonify({"message": "Username already taken"}), 400
        user.username = data['username']

    try:
        db.session.commit()  # Commit changes to the database
        return jsonify({
            "message": "Profile updated successfully!",
            "user": {
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "profile_picture": user.profile_picture
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating profile: {e}")
        return jsonify({"message": "An error occurred while updating the profile"}), 500


@authbp.route('/profile_picture', methods=['GET'])
@jwt_required()
def get_profile_picture():
    user_id = get_jwt_identity()  # Get the user ID from the token
    user = User.query.get(user_id)  # Fetch the current user

    if not user or not user.profile_picture:
        print("Profile picture not found for user:", user_id)
        return jsonify({"message": "Profile picture not found"}), 404

    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], user.profile_picture)
    
    # Check if the file exists before serving it
    if not os.path.isfile(file_path):
        print("File does not exist:", file_path)
        return jsonify({"message": "Profile picture not found"}), 404

    print("Serving profile picture from:", file_path)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], user.profile_picture)

