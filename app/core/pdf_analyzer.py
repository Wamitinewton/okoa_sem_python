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
    return [line.strip() for line in text.split("\n") if line.strip()]


def get_answer(question: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant answering exam-style questions clearly."},
            {"role": "user", "content": question},
        ],
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()


def create_answered_pdf(questions: list[str]) -> BytesIO:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50
    for q in questions:
        ans = get_answer(q)
        text = f"Q: {q}\nA: {ans}\n"
        for line in text.split("\n"):
            c.drawString(50, y, line)
            y -= 20
            if y < 50:
                c.showPage()
                y = height - 50
    c.save()
    buffer.seek(0)
    return buffer