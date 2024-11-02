from flask import Flask, request, jsonify, Blueprint
from .models import Flashcard
from .. import db
from flask_jwt_extended import jwt_required, get_jwt_identity

flashcards_bp = Blueprint('flashcard', __name__)

@flashcards_bp.route('/flashcards/create', methods=['POST'])
@jwt_required()
def create_flashcard():
    data = request.get_json()
    user_id = get_jwt_identity()  # Get the user ID from the JWT token
    new_flashcard = Flashcard(
        title=data['title'],
        content=data['content'],
        user_id=user_id
    )
    db.session.add(new_flashcard)
    db.session.commit()
    return jsonify({'message': 'Flashcard created successfully'}), 201

@flashcards_bp.route('/flashcards/delete/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_flashcard(id):
    user_id = get_jwt_identity()  # Get the user ID from the JWT token
    flashcard = Flashcard.query.get(id)
    
    # Check if flashcard exists and belongs to the user
    if flashcard and flashcard.user_id == user_id:
        db.session.delete(flashcard)
        db.session.commit()
        return jsonify({'message': 'Flashcard deleted successfully'}), 200
    elif flashcard is None:
        return jsonify({'message': 'Flashcard not found'}), 404
    else:
        return jsonify({'message': 'Unauthorized'}), 403

@flashcards_bp.route('/flashcards/search', methods=['GET'])
@jwt_required()
def search_flashcards():
    title = request.args.get('title')
    user_id = get_jwt_identity()  # Get the user ID from the JWT token
    flashcards = Flashcard.query.filter(
        Flashcard.title.ilike(f"%{title}%"),
        Flashcard.user_id == user_id  # Ensure only user's flashcards are searched
    ).all()
    results = [{'id': f.id, 'title': f.title, 'content': f.content} for f in flashcards]
    return jsonify(results), 200

@flashcards_bp.route('/flashcards', methods=['GET'])
@jwt_required()
def get_flashcards_by_user():
    user_id = get_jwt_identity()  # Get the user ID from the JWT token
    flashcards = Flashcard.query.filter_by(user_id=user_id).all()
    results = [{'id': f.id, 'title': f.title, 'content': f.content} for f in flashcards]
    return jsonify(results), 200

@flashcards_bp.route('/flashcards/edit/<int:id>', methods=['PUT'])
@jwt_required()
def edit_flashcard(id):
    user_id = get_jwt_identity() # Get the user ID from the JWT token
    flashcard = Flashcard.query.get(id)

    # Check if the flashcard exists and belongs to the user
    if flashcard and flashcard.user_id == user_id:
        data = request.get_json()
        flashcard.title = data.get('title', flashcard.title)
        flashcard.content = data.get('content', flashcard.content)
        db.session.commit()
        return jsonify({'message': 'Flashcard updated successfully'}), 200
    elif flashcard is None:
        return jsonify({'message': 'Flashcard not found'}), 404
    else:
        return jsonify({'message': 'Unauthorized'}), 403