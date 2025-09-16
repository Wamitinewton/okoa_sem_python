import asyncio
import json
import re
from typing import List, Dict
from PyPDF2 import PdfReader
from io import BytesIO
from openai import AsyncOpenAI
from app.core.config import settings

# Initialize async OpenAI client
aclient = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def extract_questions(file_bytes: bytes) -> List[str]:
    """
    Improved question extraction using a two-step approach:
    1. Extract text from PDF with better structure preservation
    2. Use OpenAI to identify and extract questions from the text
    """
    # Extract text from PDF
    reader = PdfReader(BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n\n"
    
    # Use OpenAI to identify questions in the text
    prompt = """
    Analyze the following exam paper text and extract ALL questions. 
    Return ONLY a JSON array of question strings, with no additional text.
    
    Guidelines:
    1. Include both main questions and sub-questions (a, b, c, etc.)
    2. Group multi-line questions into single entries
    3. Exclude headers, footers, instructions, and other non-question content
    4. Preserve the exact wording of questions
    5. Include questions that end with question marks and those that are imperative (e.g., "Explain", "Discuss")
    
    Text to analyze:
    """
    
    # Truncate text if too long (to avoid token limits)
    max_text_length = 12000  # Adjust based on model limits
    if len(text) > max_text_length:
        text = text[:max_text_length] + "... [text truncated]"
    
    try:
        response = await aclient.chat.completions.create(
            model="gpt-3.5-turbo",  # Using faster model for extraction
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts questions from exam papers. Always return valid JSON."},
                {"role": "user", "content": prompt + text},
            ],
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("questions", [])
    
    except Exception as e:
        # Fallback to basic extraction if AI extraction fails
        print(f"AI extraction failed: {e}, using fallback")
        return fallback_extract_questions(text)

def fallback_extract_questions(text: str) -> List[str]:
    """
    Fallback method for question extraction if AI extraction fails
    """
    # Split text into lines and remove empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    questions = []
    current_question = []
    
    # Patterns that indicate the start of a question
    question_patterns = [
        r'^\d+[\.\)]',  # Number followed by dot or parenthesis
        r'^\([a-z]\)',  # Letter in parenthesis (sub-questions)
        r'^[a-z]\)',    # Letter followed by parenthesis
        r'^[IVX]+\.',   # Roman numerals
        r'^Question',   # Word "Question"
        r'^Q\.',        # Abbreviation "Q."
    ]
    
    # Patterns that indicate non-question content
    exclude_patterns = [
        r'page\s+\d+',
        r'university|college|school|institution',
        r'examination|paper|test',
        r'instructions|direction|guideline',
        r'time|hours|minutes',
        r'maximum|minimum|marks',
        r'candidate|name|registration',
        r'answer all questions',
        r'^[\d\s]+$',  # Lines with only numbers/whitespace
    ]
    
    for i, line in enumerate(lines):
        # Skip excluded patterns
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in exclude_patterns):
            continue
            
        # Check if this line starts a new question
        is_question_start = any(re.search(pattern, line) for pattern in question_patterns)
        
        # Check if line contains question indicators
        has_question_content = (
            any(keyword in line.lower() for keyword in [
                'what', 'how', 'why', 'when', 'where', 'who', 'which',
                'explain', 'describe', 'discuss', 'identify', 'analyze',
                'compare', 'contrast', 'evaluate', 'define', 'outline',
                'give', 'list', 'state', 'mention', 'write'
            ]) or line.strip().endswith('?')
        )
        
        if is_question_start or (has_question_content and len(current_question) == 0):
            # If we have a current question, save it
            if current_question:
                questions.append(' '.join(current_question))
                current_question = []
            
            current_question.append(line)
        elif current_question and (has_question_content or len(line.split()) > 3):
            # Continue building the current question
            current_question.append(line)
        elif current_question:
            # End of question reached
            questions.append(' '.join(current_question))
            current_question = []
    
    # Add the last question if exists
    if current_question:
        questions.append(' '.join(current_question))
    
    return questions

async def get_answers_batch(questions: List[str]) -> List[str]:
    """
    Get answers for multiple questions in a single API call
    """
    if not questions:
        return []
    
    # Format questions for batch processing
    questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
    
    prompt = f"""
    You are an expert examiner providing model answers to exam questions.
    Provide clear, concise answers to each question below.
    Each answer should be approximately 50-100 words.
    
    Questions:
    {questions_text}
    
    Provide your answers as a JSON object with the following format:
    {{
      "answers": [
        "Answer to question 1",
        "Answer to question 2",
        ...
      ]
    }}
    """
    
    try:
        response = await aclient.chat.completions.create(
            model="gpt-4o",  # Using more capable model for answers
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides accurate exam answers. Always return valid JSON."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=250 * len(questions),  # Allocate tokens based on question count
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("answers", [])
    
    except Exception as e:
        print(f"Batch processing failed: {e}")
        # Fallback to individual processing if batch fails
        return await get_answers_individual(questions)

async def get_answers_individual(questions: List[str]) -> List[str]:
    """
    Fallback: Get answers for questions individually
    """
    answers = []
    for q in questions:
        try:
            response = await aclient.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant answering exam questions concisely."},
                    {"role": "user", "content": q},
                ],
                max_tokens=200,
            )
            answers.append(response.choices[0].message.content.strip())
        except Exception as e:
            print(f"Error processing question: {e}")
            answers.append("Unable to generate answer for this question.")
    
    return answers

def get_questions_and_answers(questions: List[str], answers: List[str]) -> Dict:
    """
    Returns questions and answers in the specified format
    """
    result = {}
    
    for i, (question, answer) in enumerate(zip(questions, answers), 1):
        result[f"question {i}"] = question
        result[f"answer {i}"] = answer
    
    return result