from flask import Flask,request,jsonify,Blueprint
from flask_jwt_extended import jwt_required,get_jwt_identity
from .models import Flashcard
from .. import db,UPLOAD_FOLDER, allowed_file
import csv
from flask import Response


flashcards_bp = Blueprint("flashcard",__name__)

@flashcards_bp.route('/flashcards', methods=['POST'])
@jwt_required() 
def create_flashcard():
    user_id = get_jwt_identity() 
    data = request.json

    # Validate input
    question = data.get('question')
    answer = data.get('answer')

    if not question or not answer:
        return jsonify({'message': 'Question and answer are required.'}), 400

    flashcard = Flashcard(user_id=user_id, question=question, answer=answer)
    db.session.add(flashcard)
    db.session.commit()

    return jsonify({'message': 'Flashcard created successfully', 'flashcard_id': flashcard.id}), 201

@flashcards_bp.route('/flashcards/<int:flashcard_id>', methods=['GET'])
def get_flashcard(flashcard_id):
    flashcard = Flashcard.query.get_or_404(flashcard_id)
    return jsonify({
        'id': flashcard.id,
        'question': flashcard.question,
        'answer': flashcard.answer,
        'user_id': flashcard.user_id,
        'created_at': flashcard.created_at
    })


@flashcards_bp.route('/flashcards/export', methods=['GET'])
@jwt_required()
def export_flashcards():
    user_id = get_jwt_identity()
    flashcards = Flashcard.query.filter_by(user_id=user_id).all()
    
    def generate():
        yield "Question,Answer\n"
        for flashcard in flashcards:
            yield f"{flashcard.question},{flashcard.answer}\n"

    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=flashcards.csv"})

@flashcards_bp.route('/flashcards/import', methods=['POST'])
@jwt_required()
def import_flashcards():
    file = request.files.get('file')
    user_id = get_jwt_identity()

    if not file or not allowed_file(file.filename):
        return jsonify({'message': 'Invalid file format'}), 400

    content = file.read().decode('utf-8').splitlines()
    flashcards_to_add = []

    for line in content[1:]:
        parts = line.split(',')
        if len(parts) != 2:
            continue 
        question, answer = parts
        flashcards_to_add.append(Flashcard(user_id=user_id, question=question, answer=answer))

    try:
        db.session.bulk_save_objects(flashcards_to_add)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Database error occurred: ' + str(e)}), 500

    return jsonify({'message': 'Flashcards imported successfully'}), 201



@flashcards_bp.route('/flashcards/<int:flashcard_id>', methods=['PUT'])
@jwt_required()
def edit_flashcard(flashcard_id):
    flashcard = Flashcard.query.get_or_404(flashcard_id)
    if flashcard.user_id != get_jwt_identity():
        return jsonify({'message': 'Unauthorized'}), 403
    
    data = request.json
    flashcard.question = data.get('question', flashcard.question)
    flashcard.answer = data.get('answer', flashcard.answer)
    db.session.commit()
    return jsonify({'message': 'Flashcard updated successfully'})

@flashcards_bp.route('/flashcards/<int:flashcard_id>', methods=['DELETE'])
@jwt_required()
def delete_flashcard(flashcard_id):
    flashcard = Flashcard.query.get_or_404(flashcard_id)
    if flashcard.user_id != get_jwt_identity():
        return jsonify({'message': 'Unauthorized'}), 403
    
    db.session.delete(flashcard)
    db.session.commit()
    return jsonify({'message': 'Flashcard deleted successfully'})

@flashcards_bp.route('/flashcards/search', methods=['GET'])
@jwt_required()
def search_flashcards():
    user_id = get_jwt_identity()
    query = request.args.get('query', '')
    flashcards = Flashcard.query.filter(
        Flashcard.user_id == user_id,
        (Flashcard.question.ilike(f'%{query}%') | Flashcard.answer.ilike(f'%{query}%'))
    ).all()
    
    return jsonify([{'id': fc.id, 'question': fc.question, 'answer': fc.answer} for fc in flashcards])
