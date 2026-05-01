import os
import uvicorn
import random
import json
import httpx
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# --- FastAPI App ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    answer: str

class GenerateRequest(BaseModel):
    knowledge: str
    topic: str

class GenerateResponse(BaseModel):
    quiz: list[QuizQuestion]

# --- Pre-defined Question Bank ---
QUESTION_BANK = {
    "recursion": [
        {
            "question": "What is the most crucial component of a recursive function to prevent infinite loops?",
            "options": ["A recursive step", "A base case", "A parameter", "A return value"],
            "answer": "B"
        }
    ],
    "loops": [
        {
            "question": "Which type of loop is best suited for iterating over a sequence of items?",
            "options": ["while loop", "for loop", "nested loop", "infinite loop"],
            "answer": "B"
        }
    ],
    "stack": [
        {
            "question": "A stack data structure operates on which principle?",
            "options": ["First-In, First-Out (FIFO)", "Last-In, First-Out (LIFO)", "First-In, Last-Out (FILO)", "Random Access"],
            "answer": "B"
        }
    ],
    "queue": [
        {
            "question": "A queue data structure operates on which principle?",
            "options": ["Last-In, First-Out (LIFO)", "First-In, First-Out (FIFO)", "Last-In, Last-Out (LILO)", "Random Access"],
            "answer": "B"
        }
    ],
    "binary search": [
        {
            "question": "What is a prerequisite for performing a binary search on a list?",
            "options": ["The list must be sorted", "The list must contain numbers", "The list must be short", "The list must be mutable"],
            "answer": "A"
        }
    ]
}


def generate_real_questions_from_text(knowledge: str, topic: str) -> list[dict]:
    """
    A more robust template-based generator that creates meaningful questions.
    This function now consistently works with and returns dictionaries.
    """
    questions = []
    normalized_topic = topic.lower()

    # Check if there's a pre-defined question for this topic
    for key, bank_questions in QUESTION_BANK.items():
        if key in normalized_topic:
            questions.extend(bank_questions)

    # Question 1: Identify the core definition
    # Looks for sentences like "A [topic] is a [definition]."
    match = re.search(r"is a (?:way|method|set|block|collection|blueprint|sequence|format|process|field|model)\s(?:of|for)\s(.+?)\.", knowledge, re.IGNORECASE)
    if match:
        definition_part = match.group(1)
        distractors = [
            "a type of computer hardware",
            "a graphical user interface element",
            "a network communication protocol",
            "a file system format"
        ]
        random.shuffle(distractors)
        options = [definition_part.capitalize()] + distractors[:3]
        random.shuffle(options)
        answer_index = options.index(definition_part.capitalize())
        questions.append({
            "question": f"Fundamentally, what is a '{topic}'?",
            "options": [f"{chr(65+i)}) {opt}" for i, opt in enumerate(options)],
            "answer": chr(65 + answer_index)
        })

    # Question 2: Find a key characteristic (e.g., LIFO, FIFO, mutable)
    key_characteristics = {
        "LIFO": "FIFO", "FIFO": "LIFO",
        "mutable": "immutable", "immutable": "mutable",
        "ordered": "unordered", "unordered": "ordered"
    }
    for char, opposite in key_characteristics.items():
        if re.search(r'\b' + char + r'\b', knowledge, re.IGNORECASE):
            options = [char.capitalize(), opposite.capitalize(), "Connection-oriented", "Stateless"]
            random.shuffle(options)
            answer_index = options.index(char.capitalize())
            questions.append({
                "question": f"Which of the following is a key characteristic of a {topic}?",
                "options": [f"{chr(65+i)}) {opt}" for i, opt in enumerate(options)],
                "answer": chr(65 + answer_index)
            })
            break # Add only one such question

    # Question 3: True/False from a sentence in the text
    sentences = [s.strip() for s in knowledge.split('.') if len(s.strip()) > 20]
    if sentences:
        true_statement = random.choice(sentences)
        # Make a plausible false statement by negating a keyword
        false_statement = true_statement.replace(" is ", " is not ").replace(" are ", " are not ").replace(" must ", " must not ")
        
        options = [true_statement, false_statement]
        random.shuffle(options)
        is_true_first = options[0] == true_statement
        
        questions.append({
            "question": f"Which of the following statements about {topic} is TRUE?",
            "options": [f"A) {options[0]}", f"B) {options[1]}"],
            "answer": "A" if is_true_first else "B"
        })

    # Fallback if no questions were generated
    if not questions:
        return [{
            "question": f"Is '{topic}' a concept in computer science?",
            "options": ["A) Yes", "B) No"],
            "answer": "A"
        }]

    # Clean up options and return unique questions
    final_questions = []
    seen_questions = set()
    for q in questions:
        if q["question"] not in seen_questions:
            # Ensure options are just the text, not "A) text"
            cleaned_options = [re.sub(r'^[A-D]\)\s*', '', opt) for opt in q["options"]]
            q["options"] = cleaned_options
            final_questions.append(q)
            seen_questions.add(q["question"])

    return final_questions[:3] # Return max 3 questions


# --- API Endpoints ---
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/meta")
async def meta():
    return {
        "name": "quiz-svc",
        "skill": "quiz",
        "description": "P2P quiz generation agent"
    }

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    generated_questions = generate_real_questions_from_text(request.knowledge, request.topic)

    # Ensure we always return a valid list of Pydantic models
    if not generated_questions:
        quiz_questions = [QuizQuestion(question="No quiz could be generated for this topic.", options=["OK"], answer="A")]
    else:
        # Convert dicts to QuizQuestion objects
        quiz_questions = [QuizQuestion(**q) for q in generated_questions]


    return GenerateResponse(quiz=quiz_questions)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7102)
