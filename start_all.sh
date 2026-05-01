#!/bin/bash

# This script starts the entire AgentNetwork Study Pipeline stack.
# 1. Starts two local anet P2P daemons.
# 2. Starts the three Python FastAPI agents in the background.
# 3. Registers the agents to the P2P mesh.
# 4. Starts a simple Python HTTP server for the frontend.

# --- Cleanup previous runs ---
echo "--- Cleaning up previous processes ---"
# Kill any running agents or servers on the specified ports
fuser -k 7101/tcp || true
fuser -k 7102/tcp || true
fuser -k 7103/tcp || true
fuser -k 8080/tcp || true
# Stop the anet daemons
bash scripts/two-node.sh stop || true
echo "Cleanup complete."
echo ""

# --- Start anet Daemons ---
echo "--- Starting anet P2P Daemons ---"
if [ ! -f "scripts/two-node.sh" ]; then
    echo "Error: scripts/two-node.sh not found."
    echo "Please copy it from the anet-p2p-starter-kit."
    exit 1
fi
bash scripts/two-node.sh start
echo "Daemons started. Waiting for them to initialize..."
sleep 3 # Give daemons time to start up and generate tokens
echo ""

# --- Start Agents ---
echo "--- Starting FastAPI Agents ---"
if [ ! -d "agents" ]; then
    echo "Error: 'agents' directory not found."
    exit 1
fi

cd agents
echo "Starting Knowledge Agent (port 7101)..."
python3 knowledge_agent.py &
KNOWLEDGE_PID=$!

echo "Starting Quiz Agent (port 7102)..."
python3 quiz_agent.py &
QUIZ_PID=$!

echo "Starting Orchestrator Agent (port 7103)..."
python3 orchestrator_agent.py &
ORCH_PID=$!
cd ..

echo "Agents starting in background. Waiting for them to initialize..."
sleep 4 # Give servers time to start
echo ""

# --- Register Agents ---
echo "--- Registering Agents to P2P Mesh ---"
if [ ! -f "register_agents.sh" ]; then
    echo "Error: register_agents.sh not found."
    exit 1
fi
bash register_agents.sh
sleep 1
echo ""

# --- Start Frontend ---
echo "--- Starting Frontend Server ---"
if [ ! -d "frontend" ]; then
    echo "Error: 'frontend' directory not found."
    exit 1
fi
cd frontend
echo "Starting HTTP server on port 8080..."
python3 -m http.server 8080 &
FRONTEND_PID=$!
cd ..
echo ""

# --- Final Status ---
echo "================================================"
echo "✅ Everything is running!"
echo "================================================"
echo ""
echo "   - Frontend UI:      http://localhost:8080"
echo "   - Orchestrator API: http://localhost:7103"
echo "   - Knowledge API:    http://localhost:7101"
echo "   - Quiz API:         http://localhost:7102"
echo ""
echo "   - P2P Daemon 1:     http://127.0.0.1:13921"
echo "   - P2P Daemon 2:     http://127.0.0.1:13922"
echo ""
echo "Open http://localhost:8080 in your browser to use the application."
echo ""
echo "To stop everything, run: bash scripts/two-node.sh stop && fuser -k 8080/tcp"
echo "================================================"
