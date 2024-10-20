from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .. import db
from .models import Flashcard

flashcards_bp = Blueprint('flashcards', __name__)

@flashcards_bp.route('/flashcards', methods=['POST'])
@jwt_required()
def create_flashcard():
    user_id = get_jwt_identity()
    data = request.get_json()

    question = data.get('question')
    answer = data.get('answer')

    if not question or not answer:
        return jsonify({"message": "Question and answer are required"}), 400

    flashcard = Flashcard(user_id=user_id, question=question, answer=answer)
    db.session.add(flashcard)
    db.session.commit()

    return jsonify({"message": "Flashcard created", "flashcard_id": flashcard.id}), 201

@flashcards_bp.route('/flashcards', methods=['GET'])
@jwt_required()
def get_flashcards():
    user_id = get_jwt_identity()
    flashcards = Flashcard.query.filter_by(user_id=user_id).all()

    return jsonify([{
        'id': flashcard.id,
        'question': flashcard.question,
        'answer': flashcard.answer,
        'created_at': flashcard.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for flashcard in flashcards]), 200
