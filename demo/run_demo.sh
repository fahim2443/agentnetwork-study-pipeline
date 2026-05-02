#!/bin/bash

# This script runs an automated command-line demo of the AgentNetwork Study Pipeline.
# It verifies that all services are running and then executes a full P2P workflow.

set -e

ORCHESTRATOR_URL="http://localhost:7103"
KNOWLEDGE_URL="http://localhost:7101"
QUIZ_URL="http://localhost:7102"
EXPLANATION_URL="http://localhost:7104"

# Set up anet env
export ANET_BASE_URL=http://127.0.0.1:13921
export ANET_TOKEN=$(HOME=/tmp/anet-p2p-u1 anet auth token print)
export HOME=/tmp/anet-p2p-u1

echo "=== AgentNetwork Study Pipeline Demo ==="
echo "========================================"
echo ""

echo "Step 1: Checking all agents are alive..."
curl -s --fail $KNOWLEDGE_URL/health | python3 -m json.tool
echo "✓ Knowledge Agent is alive."
curl -s --fail $QUIZ_URL/health | python3 -m json.tool
echo "✓ Quiz Agent is alive."
curl -s --fail $EXPLANATION_URL/health | python3 -m json.tool
echo "✓ Explanation Agent is alive."
curl -s --fail $ORCHESTRATOR_URL/health | python3 -m json.tool
echo "✓ Orchestrator Agent is alive."
echo ""

echo "Step 2: Discovering services on P2P mesh..."
anet svc list
echo "✓ Service list retrieved."
echo ""

echo "Step 3: Running full study pipeline for topic 'Python Stack Data Structure'..."
curl -s -X POST $ORCHESTRATOR_URL/study \
  -H "Content-Type: application/json" \
  -d '{"topic": "Python Stack Data Structure"}' | python3 -m json.tool
echo ""

echo "Step 4: Calling explanation agent for a wrong answer..."
curl -s -X POST $ORCHESTRATOR_URL/explain \
  -H "Content-Type: application/json" \
  -d '{
    "question": "A stack data structure operates on which principle?",
    "correct_answer": "LIFO",
    "user_answer": "FIFO",
    "topic": "stack"
  }' | python3 -m json.tool
echo ""

echo "Step 5: Auditing P2P service calls..."
anet svc audit --limit 10
echo ""


echo "✅ Demo complete! Pipeline working end-to-end over P2P mesh."
echo "============================================================"
