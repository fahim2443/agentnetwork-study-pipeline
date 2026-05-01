#!/bin/bash

# This script runs an automated command-line demo of the AgentNetwork Study Pipeline.
# It verifies that all services are running and then executes a full P2P workflow.

set -e

ORCHESTRATOR_URL="http://localhost:7103"
KNOWLEDGE_URL="http://localhost:7101"
QUIZ_URL="http://localhost:7102"

# Use the first daemon by default
ANET_DAEMON_URL="http://127.0.0.1:13921"
ANET_TOKEN_PATH="/tmp/anet-p2p-u1/.anet/api_token"

if [ ! -f "$ANET_TOKEN_PATH" ]; then
  ANET_DAEMON_URL="http://127.0.0.1:13922"
  ANET_TOKEN_PATH="/tmp/anet-p2p-u2/.anet/api_token"
fi

if [ ! -f "$ANET_TOKEN_PATH" ]; then
  echo "Error: anet API token not found."
  exit 1
fi

export ANET_BASE_URL=$ANET_DAEMON_URL
export ANET_TOKEN=$(cat $ANET_TOKEN_PATH)

echo "=== AgentNetwork Study Pipeline Demo ==="
echo "========================================"
echo ""

echo "Step 1: Checking all agents are alive..."
# Use curl's --fail flag to exit if any service is down
curl -s --fail $KNOWLEDGE_URL/health | python3 -m json.tool
echo "✓ Knowledge Agent is alive."
curl -s --fail $QUIZ_URL/health | python3 -m json.tool
echo "✓ Quiz Agent is alive."
curl -s --fail $ORCHESTRATOR_URL/health | python3 -m json.tool
echo "✓ Orchestrator Agent is alive."
echo ""

echo "Step 2: Discovering services on P2P mesh..."
export ANET_BASE_URL=http://127.0.0.1:13921
export ANET_TOKEN=$(cat /tmp/anet-p2p-u1/.anet/api_token)
export HOME=/tmp/anet-p2p-u1

# Now list
anet svc list
echo "✓ Service list retrieved."
echo ""

echo "Step 3: Running full pipeline for topic 'Python recursion'..."
# We pipe to `python3 -m json.tool` to pretty-print the JSON output
curl -s -X POST $ORCHESTRATOR_URL/study \
  -H "Content-Type: application/json" \
  -d '{"topic": "Python recursion"}' | python3 -m json.tool

echo ""
echo "✅ Demo complete! Pipeline working end-to-end over P2P mesh."
echo "============================================================"
