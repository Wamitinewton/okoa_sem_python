import shutil
import os
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from openai import OpenAI
from io import BytesIO
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def extract_questions(file_bytes: bytes) -> list[str]:
    reader = PdfReader(BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    # Filter out non-question content
    questions = []
    for line in lines:
        if is_likely_question(line):
            questions.append(line)
    
    return questions

def is_likely_question(line: str) -> bool:
    """
    Determines if a line is likely to be an actual question
    """
    line_lower = line.lower().strip()
    
    # Skip if too short (likely formatting or noise)
    if len(line) < 10:
        return False
    
    # Skip common header/footer patterns
    skip_patterns = [
        'university', 'college', 'school', 'institution',
        'p.o. box', 'tel:', 'email:', 'website:', 'phone:',
        'page', 'marks', 'time:', 'date:', 'april', 'may', 'june',
        'examination', 'degree', 'bachelor', 'semester',
        'iso', 'certified', 'certification',
        'instructions:', 'answer questions',
        'foundation of innovations'
    ]
    
    # Skip lines that are primarily institutional info
    for pattern in skip_patterns:
        if pattern in line_lower and not any(q_word in line_lower for q_word in ['what', 'how', 'why', 'explain', 'describe', 'discuss', 'identify']):
            return False
    
    # Skip lines that are just numbers, marks, or formatting
    if line.strip().endswith('marks)') or line.strip().endswith('marks'):
        if not any(q_word in line_lower for q_word in ['what', 'how', 'why', 'explain', 'describe', 'discuss', 'identify']):
            return False
    
    # Skip lines that are just question numbers without content
    if line.strip().startswith(('question', 'q.', 'a)', 'b)', 'c)', 'd)', 'e)', 'f)')) and len(line) < 30:
        return False
    
    # Include lines that contain question words or imperatives
    question_indicators = [
        'what', 'how', 'why', 'when', 'where', 'who', 'which',
        'explain', 'describe', 'discuss', 'identify', 'analyze',
        'compare', 'contrast', 'evaluate', 'define', 'outline',
        'give', 'list', 'state', 'mention', 'write'
    ]
    
    # Check if line contains question indicators
    contains_question_word = any(word in line_lower for word in question_indicators)
    
    # Check if it ends with question mark
    ends_with_question = line.strip().endswith('?')
    
    # Include if it has question indicators or ends with ?
    if contains_question_word or ends_with_question:
        return True
    
    # Skip everything else (headers, addresses, etc.)
    return False

def get_answer(questions: list[str]) -> list[str]:
    answers = []
    for q in questions:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant answering exam-style questions clearly."},
                {"role": "user", "content": q},
            ],
            max_tokens=200,
        )
        answers.append(response.choices[0].message.content.strip())
    return answers

def get_questions_and_answers(questions: list[str]) -> dict:
    """
    Returns questions and answers in the specified format
    """
    answers = get_answer(questions)
    result = {}
    
    for i, (question, answer) in enumerate(zip(questions, answers), 1):
        result[f"question {i}"] = question
        result[f"answer {i}"] = answer
    
    return result

def create_answered_pdf(questions: list[str]) -> BytesIO:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50
    
    answers = get_answer(questions)
    
    for q, a in zip(questions, answers):
        text = f"Q: {q}\nA: {a}\n"
        for line in text.split("\n"):
            c.drawString(50, y, line)
            y -= 20
            if y < 50:
                c.showPage()
                y = height - 50
    
    c.save()
    buffer.seek(0)
    return buffer