from fastapi import FastAPI, File, UploadFile, APIRouter
from fastapi.responses import FileResponse
from app.core.pdf_analyzer import extract_questions, get_answers_batch, get_questions_and_answers
import time
from typing import Any
import aiohttp

router = APIRouter()

@router.post("/analyze-pdf/")
async def analyze_pdf(file: UploadFile = File(...)):
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


@router.post("/analyze-pdf-from-url/")
async def analyze_pdf_from_url(pdf_url: str):
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(pdf_url) as response:
                if response.status != 200:
                    return {"error": "Failed to download PDF.", "status_code": response.status}
                contents = await response.read()
        
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