# Stew Backend - Flask API

The backend for the Stew collaborative study application is built using Flask. This API handles data management, authentication, and communication between the frontend and the database.

## Overview

The Stew backend serves as the foundation for the Stew application, providing essential functionalities such as user authentication, data storage, real-time communication, task management, and a doubt resolution feature using generative AI.

## Technologies Used

- **Backend Framework**: Flask
- **Database**: SQLite for local development (can be extended to other databases like PostgreSQL for production)
- **Authentication**: JSON Web Tokens (JWT)
- **Real-time Communication**: Flask-SocketIO (if applicable)
- **Data Validation**: Marshmallow or Flask-SQLAlchemy for data serialization and validation
- **Generative AI**: Google Gemini for generating answers to doubts

## API Documentation

### Base URL
The base URL for the API is:
```
http://localhost:5000
```

### Endpoints

#### User Authentication
- `POST /register`: Register a new user
- `POST /login`: Authenticate an existing user and receive a JWT

#### Timetable Management
- `GET /timetable`: Retrieve user timetables
- `POST /timetable`: Create a new timetable
- `PUT /timetable/<id>`: Update a timetable by ID
- `DELETE /timetable/<id>`: Delete a timetable by ID

#### Group Management
- `POST /groups`: Create a new study group
- `GET /groups`: Retrieve all groups for a user
- `POST /groups/<id>/members`: Add a member to a group
- `GET /groups/<id>`: Retrieve a specific group and its members
- `DELETE /groups/<id>`: Delete a group

#### Task Management
- `POST /tasks`: Create a new task
- `GET /tasks`: Retrieve all tasks for the current user
- `POST /tasks/<int:task_id>/complete`: Mark a task as completed
- `DELETE /tasks/<int:task_id>`: Delete a task
- `GET /tasks/scores`: Get total tasks, completed tasks, and total score

#### Doubt Resolution
- `POST /ask`: Ask a question and receive an answer
- `GET /history`: Retrieve the history of questions and answers

#### Flashcards Endpoints
- `POST /flashcards`: Create a new flashcard
- `GET /flashcards`: Retrieve all flashcards for the current user
- `POST /flashcards/<int:flashcard_id>/learn`: Mark a flashcard as
learned
- `DELETE /flashcards/<int:flashcard_id>`: Delete a flashcard
---

## Installation

To set up the Stew backend, follow these steps:

1. **Clone the Repository**:
   Open your terminal and run the following command to clone the repository:
   ```bash
   git clone https://github.com/iesxz-c/Stew-Server.git
   ```

2. **Navigate to the Backend Directory**:
   Change your current working directory to the backend folder:
   ```bash
   cd Stew/backend
   ```

3. **Create a Virtual Environment** (optional but recommended):
   It's a good practice to use a virtual environment to manage your dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

4. **Install the Dependencies**:
   Install the required packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the Application**:
   Start the Flask development server:
   ```bash
   flask run
   ```

6. **Open Your Browser**:
   The API will be accessible at `http://localhost:5000`.


Check out the Client-Side [Stew Client](https://github.com/iesxz-c/Stew-Client)
