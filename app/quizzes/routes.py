from flask import Blueprint, request, jsonify, current_app
from .. import db
from flask_jwt_extended import get_jwt_identity

quizzesbp = ('quizzes',__name__)