import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import re

# --- LLM Configuration ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# --- Expanded and Improved Knowledge Base ---
KNOWLEDGE_BASE = {
    "recursion": "Recursion in computer science is a method of solving a problem where the solution depends on solutions to smaller instances of the same problem. A recursive function must have a 'base case' to prevent infinite loops, and a 'recursive step' where it calls itself. It's elegant for tasks like traversing tree structures.",
    "variables": "A variable is a storage location with a symbolic name that contains some known or unknown quantity of information referred to as a value. In Python, variables are dynamically typed, meaning you don't have to declare their type. For example, `x = 10` binds the name 'x' to an integer object with the value 10.",
    "loops": "Loops are a fundamental control structure used to repeat a block of code. Python provides two main types: `for` loops, which iterate over a sequence (like a list, tuple, or string), and `while` loops, which execute as long as a specified condition is true. They are essential for processing collections of data.",
    "functions": "A function is a named, reusable block of code that performs a specific, well-defined task. Functions improve code modularity and reusability. They are defined with the `def` keyword in Python, can accept input parameters (arguments), and can return a value using the `return` statement.",
    "lists": "A Python list is an ordered, mutable (changeable) collection of items, enclosed in square brackets `[]`. Lists can hold items of different data types. Elements can be accessed by their index, and lists support various methods like `append()`, `pop()`, and `sort()`.",
    "dictionaries": "A dictionary in Python is an unordered, mutable collection that stores data in key-value pairs. Defined with curly braces `{}`, each key must be unique and is used to access its associated value. Dictionaries offer fast lookups, making them ideal for data retrieval.",
    "classes": "In Object-Oriented Programming (OOP), a class is a blueprint for creating objects. It defines attributes (data) and methods (functions) that its objects will have. An object is an instance of a class. For example, a `Car` class could have attributes like `color` and methods like `drive()`.",
    "algorithms": "An algorithm is a finite sequence of well-defined, computer-implementable instructions, typically to solve a class of problems or to perform a computation. Good algorithms are correct, efficient in terms of time and space, and easy to understand and implement.",
    "data structures": "A data structure is a specific format for organizing, processing, retrieving, and storing data. It determines how data is accessed and how operations can be performed on it. Common examples include arrays, linked lists, stacks, queues, trees, and graphs.",
    "sorting": "Sorting is the process of arranging items in a particular order, such as ascending or descending. Common algorithms include Bubble Sort (simple but inefficient), Merge Sort (efficient, stable, divide-and-conquer), and Quick Sort (very fast on average, but not stable).",
    "binary search": "Binary search is an efficient algorithm for finding an item from a sorted list. It works by repeatedly dividing the search interval in half. It compares the target value to the middle element; if they are not equal, the half in which the target cannot lie is eliminated, and the search continues on the remaining half.",
    "linked list": "A linked list is a linear data structure where elements are not stored contiguously. Instead, each element (a 'node') contains its data and a pointer (or 'link') to the next node in the sequence. This allows for efficient insertions and deletions from any position.",
    "stack": "A stack is a linear data structure that follows the Last-In, First-Out (LIFO) principle. The last element added is the first one to be removed. It has two main operations: `push` (adds an element to the top) and `pop` (removes the element from the top).",
    "queue": "A queue is a linear data structure that follows the First-In, First-Out (FIFO) principle. The first element added is the first one to be removed. Its main operations are `enqueue` (adds an element to the rear) and `dequeue` (removes an element from the front).",
    "machine learning": "Machine learning (ML) is a field of artificial intelligence (AI) that gives computers the ability to learn without being explicitly programmed. Algorithms are trained on data to find patterns, make predictions, or classify information. Subfields include supervised, unsupervised, and reinforcement learning.",
    "neural network": "A neural network is a machine learning model inspired by the structure of the human brain. It consists of interconnected nodes ('neurons') organized in layers. They are powerful for finding complex patterns in data, enabling tasks like image recognition, natural language processing, and forecasting."
}

# --- FastAPI App ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RetrieveRequest(BaseModel):
    topic: str

class RetrieveResponse(BaseModel):
    knowledge: str
    source: str

# --- Helper Functions ---

def get_knowledge_from_llm(topic: str) -> str:
    try:
        response = httpx.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": "You are a CS tutor. Explain topics clearly in 3-4 sentences suitable for beginners. Be concrete and specific."},
                    {"role": "user", "content": f"Explain '{topic}' in computer science in 3-4 sentences."}
                ],
                "max_tokens": 200
            },
            timeout=15
        )
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[LLM] error: {e}")
        return f"{topic} is an important concept in computer science. It involves structured problem-solving approaches used in software development."

def find_knowledge(topic: str) -> str | None:
    """
    More robust, case-insensitive, and word-boundary-aware search for a topic.
    """
    normalized_topic = topic.lower().strip()
    
    # 1. Direct key match (most efficient)
    if normalized_topic in KNOWLEDGE_BASE:
        return KNOWLEDGE_BASE[normalized_topic]
        
    # 2. Search for topic as a whole word in keys
    # Example: "stack" should match "stack & queue"
    for key, value in KNOWLEDGE_BASE.items():
        if re.search(r'\b' + re.escape(normalized_topic) + r'\b', key):
            return value
            
    # 3. Simple alias matching
    aliases = {
        "python recursion": "recursion", "recursive function": "recursion",
        "python variables": "variables", "declare variable": "variables",
        "for loop": "loops", "while loop": "loops", "iteration": "loops",
        "python functions": "functions", "define function": "functions",
        "python lists": "lists", "arrays": "lists",
        "python dict": "dictionaries", "hash map": "dictionaries",
        "python classes": "classes", "object oriented programming": "classes", "oop": "classes",
        "stacks": "stack", "queues": "queue",
        "ml": "machine learning", "ai": "machine learning",
        "ann": "neural network"
    }
    if normalized_topic in aliases:
        return KNOWLEDGE_BASE[aliases[normalized_topic]]

    # 4. If no match, return None
    return None

# --- API Endpoints ---

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/meta")
async def meta():
    return {
        "name": "knowledge-svc",
        "skill": "knowledge",
        "description": "P2P knowledge retrieval agent for CS topics"
    }

@app.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(request: RetrieveRequest):
    knowledge = find_knowledge(request.topic)
    source = "agent-knowledge-base"

    if not knowledge:
        source = "agent-knowledge-llm"
        knowledge = get_knowledge_from_llm(request.topic)

    return RetrieveResponse(knowledge=knowledge, source=source)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7101)
