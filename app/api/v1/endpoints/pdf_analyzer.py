from fastapi import FastAPI, File, UploadFile,APIRouter
from fastapi.responses import FileResponse
from app.core.pdf_analyzer import extract_questions,create_answered_pdf,get_answer


router = APIRouter()

@router.post("/analyze-pdf/{user_id}/")
async def analyze_pdf(user_id:int, file: UploadFile = File(...)):
    # Read file into memory
    contents = await file.read()

    # Extract questions
    questions = extract_questions(contents)

    answer = get_answer(questions)
     
    # Generate answered PDF in memory
    answered_pdf = create_answered_pdf(answer)

    # Send back as download
    return FileResponse(
        path=answered_pdf,
        media_type="application/pdf",
        filename=f"{user_id}_answered.pdf"
    )