# 🔗 AgentNetwork Study Pipeline

A 4-agent P2P learning system built on AgentNetwork mesh

## Architecture

```
Daemon-1: [Orchestrator] ←→ P2P Mesh ←→ [Knowledge Agent]
Daemon-2: [Quiz Agent]     ←→ P2P Mesh ←→ [Explanation Agent]
```

## Quick Start

```bash
git clone <repo>
cp .env.example .env  # add your OpenRouter key
bash start_all.sh
```

## How P2P Works

The orchestrator uses `anet svc discover` to locate available services by skill and `anet svc call` to invoke them across the mesh. That keeps the agents loosely coupled, so the pipeline can discover and call the right service without hardcoded host routing.

## 4-Agent Pipeline

- Orchestrator: receives the user topic, discovers collaborators, and coordinates the study flow.
- Knowledge Agent: retrieves or generates the explanation for the requested topic.
- Quiz Agent: turns the knowledge into multiple-choice questions.
- Explanation Agent: explains why a wrong answer is incorrect and provides a useful tip.

## Features

- LLM knowledge retrieval
- MCQ generation
- Wrong answer explanation
- Learning path suggestions
- Animated P2P visualization

#AgentNetwork

