#!/bin/bash
# This script registers the 3 study pipeline agents to the anet P2P mesh.
# It assumes a local daemon is running and its API token is available.

# Fail on any error
set -e

# --- Configuration ---
# Use the first daemon by default
ANET_DAEMON_URL="http://127.0.0.1:13921"
ANET_TOKEN_PATH="/tmp/anet-p2p-u1/.anet/api_token"

# If the first daemon's token doesn't exist, try the second one
if [ ! -f "$ANET_TOKEN_PATH" ]; then
  echo "Token for daemon 1 not found, trying daemon 2..."
  ANET_DAEMON_URL="http://127.0.0.1:13922"
  ANET_TOKEN_PATH="/tmp/anet-p2p-u2/.anet/api_token"
fi

if [ ! -f "$ANET_TOKEN_PATH" ]; then
  echo "Error: anet API token not found in either /tmp/anet-p2p-u1 or /tmp/anet-p2p-u2."
  echo "Please ensure the anet daemons are running (e.g., via 'bash scripts/two-node.sh start')."
  exit 1
fi

export ANET_BASE_URL=$ANET_DAEMON_URL
export ANET_TOKEN=$(cat $ANET_TOKEN_PATH)

echo "--- Registering Agents to anet Mesh ($ANET_BASE_URL) ---"
echo ""

echo "1. Registering Knowledge Agent (knowledge-svc)..."
anet svc register \
  --name knowledge-svc \
  --endpoint http://127.0.0.1:7101 \
  --paths /retrieve,/health,/meta \
  --modes rr \
  --tags knowledge,education,rag \
  --skill knowledge \
  --free \
  --health-check /health \
  --description "P2P knowledge retrieval agent for CS topics"

echo ""
echo "2. Registering Quiz Agent (quiz-svc)..."
anet svc register \
  --name quiz-svc \
  --endpoint http://127.0.0.1:7102 \
  --paths /generate,/health,/meta \
  --modes rr \
  --tags quiz,education,mcq \
  --skill quiz \
  --free \
  --health-check /health \
  --description "P2P quiz generation agent"

echo ""
echo "3. Registering Orchestrator Agent (orchestrator-svc)..."
anet svc register \
  --name orchestrator-svc \
  --endpoint http://127.0.0.1:7103 \
  --paths /study,/health,/pipeline \
  --modes rr \
  --tags orchestrator,education,pipeline \
  --skill study-pipeline \
  --free \
  --health-check /health \
  --description "P2P study pipeline orchestrator — chains knowledge + quiz agents"

echo ""
echo "--------------------------------------------------"
echo "✓ All 3 agents registered to anet mesh."
echo "Verifying by listing all services:"
echo ""
anet svc list
echo "--------------------------------------------------"
