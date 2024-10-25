import requests
import os
from .pdf_reader import extract_text_from_pdf

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # Store your API key securely

def create_quiz_from_prompt(prompt):
    """Generate quiz questions based on a user prompt."""
    url = "https://gemini-api-url.com/generate-quiz"
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
    payload = {"prompt": prompt, "format": "quiz"}

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json().get("quiz_questions", [])
    else:
        raise Exception("Failed to generate quiz: " + response.text)

def create_quiz_from_pdf(pdf_path):
    """Extract text from a PDF and use it to generate quiz questions."""
    text = extract_text_from_pdf(pdf_path)
    return create_quiz_from_prompt(text)
