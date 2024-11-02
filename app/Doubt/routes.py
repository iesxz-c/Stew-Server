# app/routes/doubt.py
from flask import Blueprint, request, jsonify
from .. import db
from .models import Doubt
import google.generativeai as genai
from flask_jwt_extended import get_jwt_identity,jwt_required

api = "AIzaSyBLes-Q-_omkRl4rQbUxa79bnmlczd4vyY"
genai.configure(api_key=api)
model = genai.GenerativeModel("gemini-1.5-flash")

doubt_bp = Blueprint("doubt", __name__)

@doubt_bp.route("/ask", methods=["POST"])
@jwt_required()
def ask_doubt():
    data = request.get_json()
    question = data.get("question")
    
    if not question:
        return jsonify({"error": "Question is required"}), 400
    
    # Generate answer
    response = model.generate_content(question)
    answer = response.text
    
    # Store the question and answer in the database
    user_id = get_jwt_identity()
    new_doubt = Doubt(user_id=user_id, question=question, answer=answer)
    db.session.add(new_doubt)
    db.session.commit()
    
    return jsonify({"question": question, "answer": answer}), 200

@doubt_bp.route("/history", methods=["GET"])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    doubts = Doubt.query.filter_by(user_id=user_id).all()
    history = [{"question": doubt.question, "answer": doubt.answer} for doubt in doubts]
    return jsonify(history), 200
