from flask import Flask
from flask_socketio import SocketIO
from .config import Config, TestingConfig
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from os import path
from flask_jwt_extended import JWTManager
from datetime import timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from sqlalchemy import text

# Initialize extensions
db = SQLAlchemy()
skt = SocketIO()
migrate = Migrate()
jwt = JWTManager()
scheduler = BackgroundScheduler()

DB_NAME = 'app.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def create_app(config_name=None):
    app = Flask(__name__)

    # Load configuration
    if config_name == 'testing':
        app.config.from_object(TestingConfig)  # Use TestingConfig for testing
    else:
        app.config.from_object(Config)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=31)  # Token expiry

    # Initialize extensions
    db.init_app(app)
    skt.init_app(app, cors_allowed_origins=["http://localhost:8000"])
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Enable CORS
    CORS(app, origins=["http://localhost:8000", "http://localhost:3000"])  # Add other origins as needed

    # Register blueprints
    from .auth.routes import authbp
    from .groups.routes import groupsbp
    app.register_blueprint(authbp)
    app.register_blueprint(groupsbp)

    # Import models here to avoid circular imports
    from .goals.routes import goalsbp
    app.register_blueprint(goalsbp)

    from .flashcards.routes import flashcards_bp
    app.register_blueprint(flashcards_bp)

    # Create database if it doesn't exist
    if config_name != 'testing':
        create_database(app)
        with app.app_context():  # Ensure the app context is active
            drop_temporary_table()

    return app

def drop_temporary_table():
    # Create a connection to the database
    with db.engine.connect() as connection:
        # Check if the table exists
        result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='_alembic_tmp_flashcard';"))
        table_exists = result.fetchone()

        if table_exists:
            # If it exists, drop the table
            connection.execute(text("DROP TABLE _alembic_tmp_flashcard;"))
            print("Dropped the _alembic_tmp_flashcard table.")
        else:
            print("The _alembic_tmp_flashcard table does not exist.")

def notify_upcoming_deadlines():
    from .goals.models import Goal  # Import Goal model here to avoid circular import issues
    
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

scheduler.add_job(notify_upcoming_deadlines, 'interval', hours=1)
scheduler.start()

@skt.on('some_event')
def handle_some_event(data):
    print('Received data:', data)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_database(app):
    if not path.exists('app/' + DB_NAME):
        with app.app_context():
            db.create_all()
            print('Database created!')
