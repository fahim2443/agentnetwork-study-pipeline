# 🔗 AgentNetwork Study Pipeline

A multi-agent P2P learning system built for the AgentNetwork P2P Hackathon.

This project demonstrates a collaborative pipeline of three independent AI agents communicating over the AgentNetwork P2P mesh to create personalized learning materials.

## Architecture

The system consists of three agents that collaborate dynamically using P2P service discovery.

```
  +-----------------------------------------------------------------+
  |                        AgentNetwork P2P Mesh                    |
  |                                                                 |
  |   [ knowledge-svc ] <-----> [ quiz-svc ] <-----> [ orchestrator-svc ] |
  |   (Skill: knowledge)      (Skill: quiz)         (Skill: study-pipeline) |
  |                                                                 |
  +-----------------------------------------------------------------+
      ^                                     ^                   ^
      | anet register                       | anet register     | anet register
      |                                     |                   |
+------------------+                  +---------------+   +---------------------+
| Agent-Knowledge  |                  | Agent-Quiz    |   | Agent-Orchestrator  |
| (Port 7101)      |                  | (Port 7102)   |   | (Port 7103)         |
+------------------+                  +---------------+   +---------------------+
                                                                ^
                                                                |
                                                          HTTP /study
                                                                |
                                                        +----------------+
                                                        |   Frontend UI  |
                                                        | (Port 8080)    |
                                                        +----------------+
```

1.  **Agent-Knowledge**: A FastAPI service that provides explanations for computer science topics. It registers itself on the mesh with the `knowledge` skill.
2.  **Agent-Quiz**: A FastAPI service that generates multiple-choice questions from a given text. It registers itself with the `quiz` skill.
3.  **Agent-Orchestrator**: The main entry point. When a user requests a topic, it discovers the `knowledge` and `quiz` agents on the mesh, calls them in sequence, and returns the combined result.

## Quick Start

Get the entire pipeline running with just two commands.

**Prerequisites:**
*   Python 3.9+
*   `anet` CLI installed (`pip install agentnetwork`)

**1. Clone the repository:**

```bash
git clone https://github.com/your-username/agentnetwork-study-pipeline.git
cd agentnetwork-study-pipeline
```

**2. Install dependencies and run the startup script:**

This will start the P2P daemons, all three agents, and the frontend server.

```bash
pip install -r requirements.txt
bash start_all.sh
```

**3. Open the UI in your browser:**

Navigate to **[http://localhost:8080](http://localhost:8080)**

## How AgentNetwork P2P is Used

This project leverages the AgentNetwork framework for key P2P functionalities:

*   **Service Registration**: Each agent is a standalone microservice that registers itself on the P2P mesh using `anet svc register`. This makes it discoverable by other agents without hardcoding IP addresses or ports.
*   **Service Discovery**: The `Agent-Orchestrator` dynamically finds its collaborators using `anet svc discover --skill <name>`. This decouples the agents and allows for a flexible, resilient architecture. If a new, better `quiz` agent comes online, the orchestrator can use it without any code changes.
*   **P2P Service Calls**: Agents communicate with each other through the mesh using `anet svc call`. This abstracts away the underlying network complexity, allowing secure communication across different nodes (even on different machines).

## Demo

![Demo Screenshot](demo/screenshot.png)
*(A placeholder for the demo GIF/screenshot)*

You can also run an automated command-line demo to verify the pipeline is working:

```bash
bash demo/run_demo.sh
```

---

**Team:** The A-Team
**#AgentNetwork**

