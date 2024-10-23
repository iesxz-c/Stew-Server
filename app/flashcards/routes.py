from flask import Flask,request,jsonify,Blueprint
from flask_jwt_extended import jwt_required,get_jwt_identity
from .models import Flashcard
from .. import db,UPLOAD_FOLDER, allowed_file
from PIL import Image, ImageDraw, ImageFont
import io
from flask import send_file
import csv
from flask import Response
from PyPDF2 import PdfReader



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

    # Create an image for the flashcards
    width, height = 800, 1200
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)

    # Define the font and starting position for the text
    font = ImageFont.load_default()  # You can use a custom font here
    padding = 20
    x, y = padding, padding
    line_height = 30

    # Add title
    draw.text((x, y), "Flashcards", font=font, fill="black")
    y += line_height + padding

    # Loop through flashcards and draw them on the image
    for flashcard in flashcards:
        text = f"Q: {flashcard.question}\nA: {flashcard.answer}\n"
        draw.text((x, y), text, font=font, fill="black")
        y += line_height * 3  # Space between flashcards
        if y + line_height * 3 > height - padding:
            break  # Stops if the content exceeds the image height

    # Save the image to a BytesIO stream to send as a response
    img_io = io.BytesIO()
    image.save(img_io, 'JPEG')
    img_io.seek(0)

    # Return the image as a response
    return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name='flashcards.jpg')


@flashcards_bp.route('/flashcards/import', methods=['POST'])
@jwt_required()
def import_flashcards():
    file = request.files.get('file')
    user_id = get_jwt_identity()

    if not file or not allowed_file(file.filename):
        return jsonify({'message': 'Invalid file format'}), 400

    filename = file.filename.rsplit('.', 1)[1].lower()

    flashcards_to_add = []
    
    try:
        # Handle CSV
        if filename == 'csv':
            content = file.read().decode('utf-8').splitlines()
            reader = csv.reader(content)
            next(reader)  # Skip the header
            for row in reader:
                if len(row) == 2:
                    question, answer = row
                    flashcards_to_add.append(Flashcard(user_id=user_id, question=question, answer=answer))
        
        # Handle TXT
        elif filename == 'txt':
            content = file.read().decode('utf-8')
            lines = content.split('\n')
            for line in lines:
                if ',' in line:  # Expecting comma separated question and answer
                    question, answer = line.split(',', 1)
                    flashcards_to_add.append(Flashcard(user_id=user_id, question=question.strip(), answer=answer.strip()))
        
        # Handle PDF
        elif filename == 'pdf':
            reader = PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text()  # Extract text from all pages

            # Assuming the text has "question,answer" format on each line
            lines = text.split('\n')
            for line in lines:
                if ',' in line:
                    question, answer = line.split(',', 1)
                    flashcards_to_add.append(Flashcard(user_id=user_id, question=question.strip(), answer=answer.strip()))
        
        # Save flashcards to database
        db.session.bulk_save_objects(flashcards_to_add)
        db.session.commit()
        return jsonify({'message': 'Flashcards imported successfully'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to import flashcards: {str(e)}'}), 500



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
