from fastapi import FastAPI, File, UploadFile, APIRouter
from fastapi.responses import FileResponse
from app.core.pdf_analyzer import extract_questions, get_answers_batch, get_questions_and_answers
import time

router = APIRouter()

# @router.post("/analyze-pdf/{user_id}/")
# async def analyze_pdf(user_id: int, file: UploadFile = File(...)):
#     # Read file into memory
#     contents = await file.read()
    
#     # Extract questions
#     questions = extract_questions(contents)
    
#     # Get questions and answers in the specified format
#     formatted_answers = get_questions_and_answers(questions)
    
#     return {
#         "message": "marking scheme generated successfully",
#         "answers": formatted_answers
#     }

@router.post("/analyze-pdf/{user_id}/")
async def analyze_pdf(user_id: int, file: UploadFile = File(...)):
    start_time = time.time()
    
    contents = await file.read()
    questions = await extract_questions(contents)
    answers = await get_answers_batch(questions)
    
    if len(answers) < len(questions):
        answers.extend(["Answer not available."] * (len(questions) - len(answers)))
    
    formatted_answers = get_questions_and_answers(questions, answers)
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    return {
        "message": "marking scheme generated successfully",
        "answers": formatted_answers,
        "time_taken_seconds": elapsed_time
    }
