import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import json
from dotenv import load_dotenv

# Load .env from project root (one level up from agents/)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# --- LLM Configuration ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

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
class ExplainRequest(BaseModel):
    question: str
    correct_answer: str
    user_answer: str
    topic: str

class ExplainResponse(BaseModel):
    explanation: str
    tip: str

# --- Helper Functions ---
def get_explanation_from_llm(req: ExplainRequest) -> dict:
    try:
        prompt = f"""The student answered '{req.user_answer}' but the correct answer is '{req.correct_answer}' for this question: '{req.question}'.
Explain in 2-3 sentences why '{req.correct_answer}' is correct and why the student might have been confused. End with one practical tip to remember this."""

        response = httpx.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-chat",
                "messages": [
                    {"role": "system", "content": "You are a helpful computer science tutor. Be concise and encouraging."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 250
            },
            timeout=20
        )
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        
        # Split explanation and tip
        parts = content.rsplit("Tip:", 1)
        if len(parts) == 2:
            explanation = parts[0].strip()
            tip = parts[1].strip()
        else:
            explanation = content
            tip = "Practice with more examples to solidify your understanding."

        return {"explanation": explanation, "tip": tip}
    except Exception as e:
        print(f"[LLM explain] error: {e}")
        return {
            "explanation": f"The correct answer is '{req.correct_answer}'. Understanding the nuances of '{req.topic}' is key.",
            "tip": "Review the fundamental definition of this topic."
        }

# --- API Endpoints ---
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/meta")
async def meta():
    return {
        "name": "explanation-svc",
        "skill": "explanation",
        "description": "P2P explanation agent — explains wrong quiz answers"
    }

@app.post("/explain", response_model=ExplainResponse)
async def explain(request: ExplainRequest):
    result = get_explanation_from_llm(request)
    return ExplainResponse(**result)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7104)
