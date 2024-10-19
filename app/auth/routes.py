from flask import Blueprint, request, jsonify
from .. import db
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

authbp = Blueprint('auth', __name__)

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

@authbp.route('/profile',methods=['GET'])
@jwt_required()
def profile():
    userid = get_jwt_identity()
    user = User.query.filter_by(id=userid).first()
    return jsonify({'username': user.username})
