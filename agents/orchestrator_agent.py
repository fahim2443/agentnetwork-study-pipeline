import os
import uvicorn
import json
import subprocess
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

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
    knowledge_svc_name = discover_service("knowledge")
    
    if knowledge_svc_name:
        peer_id_k, svc_k = knowledge_svc_name
        pipeline_trace.append({"step": "Discover Knowledge Service", "status": "success", "details": f"Found '{svc_k}' on peer {peer_id_k[:20]}... via anet P2P"})
        knowledge_data = call_service_via_anet(peer_id_k, svc_k, "/retrieve", {"topic": topic})
        if knowledge_data:
            pipeline_trace.append({"step": "Call Knowledge Service (P2P)", "status": "success", "details": "Called via anet svc call (true P2P)"})
        else:
            pipeline_trace.append({"step": "Call Knowledge Service (P2P)", "status": "failed", "details": "anet call failed, attempting direct HTTP fallback"})
    else:
        pipeline_trace.append({"step": "Discover Knowledge Service", "status": "failed", "details": "Could not find service with skill 'knowledge', attempting direct HTTP fallback"})

    # Fallback to direct HTTP if P2P fails
    if not knowledge_data:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post("http://localhost:7101/retrieve", json={"topic": topic}, timeout=20.0)
                response.raise_for_status()
                knowledge_data = response.json()
                pipeline_trace.append({"step": "Call Knowledge Service (HTTP Fallback)", "status": "success", "details": "Retrieved knowledge via direct HTTP call"})
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            pipeline_trace.append({"step": "Call Knowledge Service (HTTP Fallback)", "status": "error", "details": str(e)})
            raise HTTPException(status_code=503, detail="Knowledge agent is unreachable.")

    knowledge_text = knowledge_data.get("knowledge", "Error retrieving knowledge.")

    # --- Step 2: Discover and Call Quiz Agent ---
    quiz_svc_name = discover_service("quiz")

    if quiz_svc_name:
        peer_id_q, svc_q = quiz_svc_name
        pipeline_trace.append({"step": "Discover Quiz Service", "status": "success", "details": f"Found '{svc_q}' on peer {peer_id_q[:20]}... via anet P2P"})
        quiz_data = call_service_via_anet(peer_id_q, svc_q, "/generate", {"knowledge": knowledge_text, "topic": topic})
        if quiz_data:
             pipeline_trace.append({"step": "Call Quiz Service (P2P)", "status": "success", "details": "Called via anet svc call (true P2P)"})
        else:
            pipeline_trace.append({"step": "Call Quiz Service (P2P)", "status": "failed", "details": "anet call failed, attempting direct HTTP fallback"})
    else:
        pipeline_trace.append({"step": "Discover Quiz Service", "status": "failed", "details": "Could not find service with skill 'quiz', attempting direct HTTP fallback"})

    # Fallback to direct HTTP if P2P fails
    if not quiz_data:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post("http://localhost:7102/generate", json={"knowledge": knowledge_text, "topic": topic}, timeout=30.0)
                response.raise_for_status()
                quiz_data = response.json()
                pipeline_trace.append({"step": "Call Quiz Service (HTTP Fallback)", "status": "success", "details": "Generated quiz via direct HTTP call"})
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            pipeline_trace.append({"step": "Call Quiz Service (HTTP Fallback)", "status": "error", "details": str(e)})
            raise HTTPException(status_code=503, detail="Quiz agent is unreachable.")

    quiz_questions = quiz_data.get("quiz", [])
    pipeline_trace.append({"step": "Pipeline Complete", "status": "success", "details": "Successfully generated study materials."})

    return StudyResponse(
        topic=topic,
        knowledge=knowledge_text,
        quiz=quiz_questions,
        pipeline_trace=pipeline_trace
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7103)
