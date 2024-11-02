from flask import Flask, send_from_directory, abort
from flask_socketio import SocketIO
from .config import Config, TestingConfig
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from sqlalchemy import text
import os

# Initialize extensions
db = SQLAlchemy()
skt = SocketIO()
migrate = Migrate()
jwt = JWTManager()
scheduler = BackgroundScheduler()

DB_NAME = 'app.db'
UPLOAD_FOLDER = 'C:\\Users\\akash\\Videos\\Stew\\uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv'}


def create_app(config_name=None):
    app = Flask(__name__)

    # Load configuration
    if config_name == 'testing':
        app.config.from_object(TestingConfig)  # Use TestingConfig for testing
    else:
        app.config.from_object(Config)
    
    # Configure upload folder
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        
    # JWT token expiry
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=31)

    # Initialize extensions
    db.init_app(app)
    skt.init_app(app, cors_allowed_origins=["http://localhost:8000", "http://localhost:5173"])
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Enable CORS
    CORS(app, origins=["http://localhost:8000", "http://localhost:3000", "http://localhost:5173"])

    # Register blueprints
    from .auth.routes import authbp
    from .groups.routes import groupsbp
    from .goals.routes import goalsbp
    from .Flashcard.routes import flashcards_bp
    from .timetable.routes import timetable_bp
    
    app.register_blueprint(authbp)
    app.register_blueprint(groupsbp)
    app.register_blueprint(goalsbp)
    app.register_blueprint(flashcards_bp)
    app.register_blueprint(timetable_bp)

    # Ensure database is created
    if config_name != 'testing':
        create_database(app)
        with app.app_context():
            drop_temporary_table()
          
           

    # Route for serving uploaded files
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            print(f"File {filename} not found in {app.config['UPLOAD_FOLDER']}")
            abort(404)
        print(f"Serving file from: {file_path}")
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    return app


def drop_temporary_table():
    # Create a connection to the database
    with db.engine.connect() as connection:
        # Check if the table exists
        result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='_alembic_tmp_flashcard';"))
        table_exists = result.fetchone()

        if table_exists:
            # Drop the table if it exists
            connection.execute(text("DROP TABLE _alembic_tmp_flashcard;"))
            print("Dropped the _alembic_tmp_flashcard table.")
        else:
            print("The _alembic_tmp_flashcard table does not exist.")


def notify_upcoming_deadlines():
    from .goals.models import Goal  # Import Goal model to avoid circular import issues
    
    now = datetime.utcnow()
    upcoming_deadline = now + timedelta(hours=24)
    
    try:
        goals = Goal.query.filter(Goal.deadline <= upcoming_deadline, Goal.is_completed == False).all()

        for goal in goals:
            user_id = goal.user_id
            skt.emit('notification', {
                'message': f"Upcoming deadline for goal: {goal.title}",
                'goal_id': goal.id,
                'deadline': goal.deadline.strftime('%Y-%m-%d %H:%M:%S')
            }, room=user_id)
    except Exception as e:
        print(f"Error notifying upcoming deadlines: {e}")

# Schedule the job
scheduler.add_job(notify_upcoming_deadlines, 'interval', hours=1)
scheduler.start()


@skt.on('some_event')
def handle_some_event(data):
    print('Received data:', data)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def create_database(app):
    db_path = os.path.join(app.instance_path, DB_NAME)
    if not os.path.exists(db_path):
        with app.app_context():
            db.create_all()
            print('Database created!')




