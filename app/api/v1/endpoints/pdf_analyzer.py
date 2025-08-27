from fastapi import FastAPI, File, UploadFile, APIRouter
from fastapi.responses import FileResponse
from app.core.pdf_analyzer import extract_questions, create_answered_pdf, get_answer, get_questions_and_answers

router = APIRouter()

@router.post("/analyze-pdf/{user_id}/")
async def analyze_pdf(user_id: int, file: UploadFile = File(...)):
    # Read file into memory
    contents = await file.read()
    
    # Extract questions
    questions = extract_questions(contents)
    
    # Get questions and answers in the specified format
    formatted_answers = get_questions_and_answers(questions)
    
    return {
        "message": "marking scheme generated successfully",
        "answers": formatted_answers
    }