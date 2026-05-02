#!/bin/bash
# This script registers the agents to the anet P2P mesh.

# Fail on any error
set -e

echo "--- Registering Agents to anet Mesh ---"
echo ""

# --- Register Knowledge Agent to Daemon 1 ---
echo "1. Registering Knowledge Agent (knowledge-svc) to daemon-1..."
ANET_BASE_URL=http://127.0.0.1:13921 \
ANET_TOKEN=$(HOME=/tmp/anet-p2p-u1 anet auth token print) \
HOME=/tmp/anet-p2p-u1 anet svc register \
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

# --- Register Quiz Agent to Daemon 2 ---
echo "2. Registering Quiz Agent (quiz-svc) to daemon-2..."
ANET_BASE_URL=http://127.0.0.1:13922 \
ANET_TOKEN=$(HOME=/tmp/anet-p2p-u2 anet auth token print) \
HOME=/tmp/anet-p2p-u2 anet svc register \
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

# --- Register Explanation Agent to Daemon 2 ---
echo "3. Registering Explanation Agent (explanation-svc) to daemon-2..."
ANET_BASE_URL=http://127.0.0.1:13922 \
ANET_TOKEN=$(HOME=/tmp/anet-p2p-u2 anet auth token print) \
HOME=/tmp/anet-p2p-u2 anet svc register \
  --name explanation-svc \
  --endpoint http://127.0.0.1:7104 \
  --paths /explain,/health,/meta \
  --modes rr \
  --tags explanation,education,feedback \
  --skill explanation \
  --free \
  --health-check /health \
  --description "P2P explanation agent — explains wrong quiz answers"

echo ""

# --- Register Orchestrator Agent to Daemon 1 ---
echo "4. Registering Orchestrator Agent (orchestrator-svc) to daemon-1..."
ANET_BASE_URL=http://127.0.0.1:13921 \
ANET_TOKEN=$(HOME=/tmp/anet-p2p-u1 anet auth token print) \
HOME=/tmp/anet-p2p-u1 anet svc register \
  --name orchestrator-svc \
  --endpoint http://127.0.0.1:7103 \
  --paths /study,/health,/pipeline,/explain,/learning-path \
  --modes rr \
  --tags orchestrator,education,pipeline \
  --skill study-pipeline \
  --free \
  --health-check /health \
  --description "P2P study pipeline orchestrator"

echo ""
echo "--------------------------------------------------"
echo "✓ All 4 agents registered to anet mesh."
echo "Verifying by listing all services on both daemons:"
echo ""
echo "--- Daemon 1 Services ---"
ANET_BASE_URL=http://127.0.0.1:13921 ANET_TOKEN=$(HOME=/tmp/anet-p2p-u1 anet auth token print) HOME=/tmp/anet-p2p-u1 anet svc list
echo ""
echo "--- Daemon 2 Services ---"
ANET_BASE_URL=http://127.0.0.1:13922 ANET_TOKEN=$(HOME=/tmp/anet-p2p-u2 anet auth token print) HOME=/tmp/anet-p2p-u2 anet svc list
echo "--------------------------------------------------"
