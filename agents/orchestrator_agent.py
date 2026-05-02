import os
import uvicorn
import json
import subprocess
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load .env from project root (one level up from agents/)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# --- LLM Configuration ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

print(f"[config] API key loaded: {'YES' if OPENROUTER_API_KEY else 'NO - check .env file'}")

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
class StudyRequest(BaseModel):
    topic: str

class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    answer: str

class StudyResponse(BaseModel):
    topic: str
    knowledge: str
    quiz: list[QuizQuestion]
    pipeline_trace: list[Dict[str, Any]]

class ExplainRequest(BaseModel):
    question: str
    correct_answer: str
    user_answer: str
    topic: str

class ExplainResponse(BaseModel):
    explanation: str
    tip: str

class LearningPathRequest(BaseModel):
    topic: str

class LearningPathResponse(BaseModel):
    topics: List[str]


# --- anet P2P Helper Functions ---

def discover_service(skill: str) -> tuple | None:
    try:
        token = open("/tmp/anet-p2p-u1/.anet/api_token").read().strip()
        env = {**os.environ, "ANET_BASE_URL": "http://127.0.0.1:13921",
               "ANET_TOKEN": token, "HOME": "/tmp/anet-p2p-u1"}
        result = subprocess.run(
            ["anet", "svc", "discover", "--skill", skill, "--json"],
            capture_output=True, text=True, env=env, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            results = data.get("results", [])
            if results:
                peer_id = results[0].get("peer_id", "")
                services = results[0].get("services", [])
                if peer_id and services:
                    return (peer_id, services[0]["name"])
    except Exception as e:
        print(f"[discover] error: {e}")
    return None

def call_service_via_anet(peer_id: str, service_name: str, path: str, body: dict) -> dict | None:
    try:
        token = open("/tmp/anet-p2p-u1/.anet/api_token").read().strip()
        env = {**os.environ, "ANET_BASE_URL": "http://127.0.0.1:13921",
               "ANET_TOKEN": token, "HOME": "/tmp/anet-p2p-u1"}
        result = subprocess.run(
            ["anet", "svc", "call", peer_id, service_name, path,
             "--method", "POST",
             "--header", "Content-Type=application/json",
             "--body", json.dumps(body)],
            capture_output=True, text=True, env=env, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            output = result.stdout.strip()
            json_start = output.find('{')
            if json_start != -1:
                return json.loads(output[json_start:])
        else:
            print(f"[call] failed. stderr: {result.stderr.strip()}")
    except Exception as e:
        print(f"[call] error: {e}")
    return None


# --- API Endpoints ---
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/pipeline")
async def get_pipeline_status():
    """Returns current pipeline status and registered services."""
    try:
        token_path = "/tmp/anet-p2p-u1/.anet/api_token"
        home_path = "/tmp/anet-p2p-u1"
        if not os.path.exists(token_path):
             raise FileNotFoundError("Primary anet user token not found at /tmp/anet-p2p-u1/.anet/api_token")
        
        token = open(token_path).read().strip()
        env = {**os.environ, "ANET_BASE_URL": "http://127.0.0.1:13921", "ANET_TOKEN": token, "HOME": home_path}
        
        result = subprocess.run(["anet", "svc", "list", "--json"], capture_output=True, text=True, check=True, env=env)
        services = json.loads(result.stdout) # Expecting a list
        return {"status": "ok", "registered_services": len(services), "services": services}
    except Exception as e:
        return {"status": "error", "message": str(e), "registered_services": 0}

@app.post("/study", response_model=StudyResponse)
async def study(request: StudyRequest):
    topic = request.topic
    pipeline_trace = []
    knowledge_data = None
    quiz_data = None

    # --- Step 1: Discover and Call Knowledge Agent ---
    knowledge_svc_info = discover_service("knowledge")
    
    if knowledge_svc_info:
        peer_id_k, svc_k = knowledge_svc_info
        pipeline_trace.append({"step": "Discover Knowledge Service", "status": "success", "details": f"Found '{svc_k}' on peer {peer_id_k[:12]}..."})
        knowledge_data = call_service_via_anet(peer_id_k, svc_k, "/retrieve", {"topic": topic})
        if knowledge_data:
            pipeline_trace.append({"step": "Call Knowledge Service (P2P)", "status": "success", "details": "Called via anet svc call"})
        else:
            pipeline_trace.append({"step": "Call Knowledge Service (P2P)", "status": "failed", "details": "anet call failed, attempting HTTP fallback"})
    else:
        pipeline_trace.append({"step": "Discover Knowledge Service", "status": "failed", "details": "Could not find 'knowledge' skill, attempting HTTP fallback"})

    if not knowledge_data:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post("http://localhost:7101/retrieve", json={"topic": topic}, timeout=20.0)
                response.raise_for_status()
                knowledge_data = response.json()
                pipeline_trace.append({"step": "Call Knowledge Service (HTTP Fallback)", "status": "success"})
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            raise HTTPException(status_code=503, detail=f"Knowledge agent unreachable: {e}")

    knowledge_text = knowledge_data.get("knowledge", "Error retrieving knowledge.")

    # --- Step 2: Discover and Call Quiz Agent ---
    quiz_svc_info = discover_service("quiz")

    if quiz_svc_info:
        peer_id_q, svc_q = quiz_svc_info
        pipeline_trace.append({"step": "Discover Quiz Service", "status": "success", "details": f"Found '{svc_q}' on peer {peer_id_q[:12]}..."})
        quiz_data = call_service_via_anet(peer_id_q, svc_q, "/generate", {"knowledge": knowledge_text, "topic": topic})
        if quiz_data:
             pipeline_trace.append({"step": "Call Quiz Service (P2P)", "status": "success", "details": "Called via anet svc call"})
        else:
            pipeline_trace.append({"step": "Call Quiz Service (P2P)", "status": "failed", "details": "anet call failed, attempting HTTP fallback"})
    else:
        pipeline_trace.append({"step": "Discover Quiz Service", "status": "failed", "details": "Could not find 'quiz' skill, attempting HTTP fallback"})

    if not quiz_data:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post("http://localhost:7102/generate", json={"knowledge": knowledge_text, "topic": topic}, timeout=30.0)
                response.raise_for_status()
                quiz_data = response.json()
                pipeline_trace.append({"step": "Call Quiz Service (HTTP Fallback)", "status": "success"})
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            raise HTTPException(status_code=503, detail=f"Quiz agent unreachable: {e}")

    quiz_questions = quiz_data.get("quiz", [])
    pipeline_trace.append({"step": "Pipeline Complete", "status": "success"})

    return StudyResponse(
        topic=topic,
        knowledge=knowledge_text,
        quiz=quiz_questions,
        pipeline_trace=pipeline_trace
    )

@app.post("/explain", response_model=ExplainResponse)
async def explain(request: ExplainRequest):
    explanation_data = None
    
    # Discover and call explanation service
    explanation_svc_info = discover_service("explanation")
    if explanation_svc_info:
        peer_id_e, svc_e = explanation_svc_info
        explanation_data = call_service_via_anet(peer_id_e, svc_e, "/explain", request.dict())

    # Fallback to direct HTTP if P2P fails
    if not explanation_data:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post("http://127.0.0.1:7104/explain", json=request.dict(), timeout=25.0)
                response.raise_for_status()
                explanation_data = response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            raise HTTPException(status_code=503, detail=f"Explanation agent unreachable: {e}")

    return ExplainResponse(**explanation_data)

@app.post("/learning-path", response_model=LearningPathResponse)
async def learning_path(request: LearningPathRequest):
    try:
        prompt = f"""Given someone just studied '{request.topic}', suggest exactly 3 related CS topics they should study next. Return ONLY a JSON array of 3 strings. Example: ["Binary Trees", "Dynamic Programming", "Graph Algorithms"]"""
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek/deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are a curriculum planner. Return only a valid JSON array of strings."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 100
                },
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            raw_content = data["choices"][0]["message"]["content"].strip()
            
            # Clean and parse the JSON
            if raw_content.startswith("```"):
                raw_content = raw_content.split("```")[1]
                if raw_content.startswith("json"):
                    raw_content = raw_content[4:]
            
            topics = json.loads(raw_content)
            if isinstance(topics, list) and len(topics) == 3 and all(isinstance(t, str) for t in topics):
                return LearningPathResponse(topics=topics)
            else:
                raise HTTPException(status_code=500, detail="LLM returned invalid format for learning path.")

    except (httpx.RequestError, httpx.HTTPStatusError, json.JSONDecodeError, IndexError) as e:
        raise HTTPException(status_code=503, detail=f"Failed to generate learning path from LLM: {e}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7103)


@app.get("/config-check")
async def config_check():
    return {
        "api_key_loaded": bool(OPENROUTER_API_KEY),
        "key_prefix": (OPENROUTER_API_KEY[:10] + "...") if OPENROUTER_API_KEY else "EMPTY"
    }
