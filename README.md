# 🤖 Deep Agent — Dynamic Multi-Agent Router

A multi-agent AI system that intelligently routes queries to specialized sub-agents (Coding, Reasoning, Math) and dynamically selects the optimal LLM model tier (Pro, Standard, Lite) based on query complexity — all at runtime.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red?logo=streamlit)
![LiteLLM](https://img.shields.io/badge/LiteLLM-Powered-green)
![Groq](https://img.shields.io/badge/Groq-API-orange)
![Gemini](https://img.shields.io/badge/Google-Gemini-blue)

---

## 🏗️ Architecture

                  ┌─────────────────┐
                  │   USER QUERY    │
                  └────────┬────────┘
                           │
                           ▼
           ┌───────────────────────────────┐
           │     🧠 ROUTER (Classify)      |
           │  Vertex Gemini 2.5 Flash lite │
           │                               │
           │  Determines:                  │
           │  1. Agent (coding/math/reason)│
           │  2. Complexity (simple/med/cx)│
           │  3. Model Tier (lite/std/pro) │
           └───┬───────────┬───────────┬───┘
               │           │           │
               ▼           ▼           ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │💻 Coding │ │🧠 Reason │ │🔢 Math   │
        │  Agent   │ │  Agent   │ │  Agent   │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │
             └──────┬─────┘────────────┘
                    │
                    ▼ (Dynamic Model Selection)
     ┌──────────────────────────────────────┐
     │ 🟢 Lite  → Gemini 2.5 Flash-Lite    │
     │           (fallback: Gemini 2.5)    │
     │ 🟠 Standard → Gemini 2.5 Flash      │
     │             (fallback: Gemini 2.5)   │
     │ 🔴 Pro  → Gemini 2.5 Pro            │
     │           (fallback: Gemini 2.5)     │
     └──────────────────────────────────────┘
                    │
                    ▼
     ┌──────────────────────────────────────┐
     │  📊 Response + Metrics + Guardrails  │
     │  Latency, Tokens, Cost, Safety      │
     └──────────────────────────────────────┘

---

## ✨ Key Features

- **🤖 Intelligent Routing** — Router classifies every query and picks the right sub-agent + model tier automatically
- **💰 Cost Optimization** — Simple tasks use lite models (cheap), complex tasks get pro models (powerful)
- **⚡ Dynamic Model Selection** — Model tier decided at runtime based on query complexity
- **🔄 Fallback Strategy** — If primary model unavailable, automatically falls back to proven stable variant
- **📊 Full Observability** — Latency, token usage, cost tracking shown for every query
- **🎯 3 Specialized Agents** — Coding, Reasoning, and Math each with fine-tuned system prompts
- **🛡️ Multi-Layer Guardrails** — Input validation, PII detection, output safety scanning, rate limiting

---

## 📊 Model Tiers

| Tier                 | Primary Model                    | Fallback Model           | Use Case                         | Cost     |
| -------------------- | -------------------------------- | ------------------------ | -------------------------------- | -------- |
| 🟢 **Lite**          | Gemini 2.5 Flash-Lite            | Gemini 2.5 Flash         | Simple tasks (math, facts)       | Lowest   |
| 🟠 **Standard**      | Gemini 2.5 Flash                 | Gemini 2.5 Flash         | Medium tasks (code, comparisons) | Medium   |
| 🔴 **Pro**           | Gemini 2.5 Pro (Experimental)    | Gemini 2.5 Pro           | Complex tasks (reasoning, design)| Highest  |
| 🔧 **Router**        | Gemini 2.5 Flash-lite               | —                        | Query classification only        | Minimal  |

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/multi-agent-router.git
cd multi-agent-router

2. Create Virtual Environment
Bash

python -m venv venv

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Mac/Linux
source venv/bin/activate

3. Install Dependencies
Bash

pip install -r requirements.txt

### 4. Set Up Vertex AI Authentication

You need Google Cloud credentials for Vertex AI. Use Application Default Credentials:

```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# OR set VERTEX_PROJECT_ID environment variable
# Windows PowerShell
$env:VERTEX_PROJECT_ID = "your-gcp-project-id"
$env:VERTEX_LOCATION = "us-central1"

# Mac/Linux
export VERTEX_PROJECT_ID="your-gcp-project-id"
export VERTEX_LOCATION="us-central1"
```

5. Run
Bash

python -m streamlit run app.py
App opens at http://localhost:8501

📁 Project Structure
text

multi-agent-router/
├── app.py              # Streamlit UI + main orchestration
├── agents.py           # Sub-agent execution + fallback logic
├── router.py           # Deep Agent query classification
├── config.py           # Model configs + API key management
├── requirements.txt    # Dependencies
├── .gitignore          # Excludes venv, cache, env files
└── README.md           # This file


🧪 Test Queries
#	Query	Expected Agent	Expected Tier
1	What is 25 * 48?	Math	🟢 Lite
2	Prove that √2 is irrational	Math	🔴 Pro
3	Write a function to add two numbers	Coding	🟢 Lite
4	Implement binary search in Python	Coding	🟠 Standard
5	Design a thread-safe LRU cache with TTL expiration	Coding	🔴 Pro
6	What is the capital of Japan?	Reasoning	🟢 Lite
7	Compare SQL vs NoSQL for e-commerce	Reasoning	🟠 Standard
8	Analyze microservices vs monolith for a 5-person startup	Reasoning	🔴 Pro
9	Solve 3x² - 12x + 9 = 0	Math	🟠 Standard
10	Implement a sliding window rate limiter with async support	Coding	🔴 Pro
💰 Why Dynamic Routing Matters
text

Example: "What is 2 + 2?"

┌────────────────┬──────────┬──────────┐
│ Model          │ Cost/1k  │ Latency  │
├────────────────┼──────────┼──────────┤
│ 🔴 Pro (70B)   │ $0.0001  │ ~3000ms  │
│ 🟠 Std (8B)    │ $0.0003  │ ~800ms   │
│ 🟢 Lite        │ $0.00125 │ ~400ms   │ ← Selected
└────────────────┴──────────┴──────────┘

Savings: ~90% cost, ~85% faster vs Pro
Quality: Identical for this simple task
🔄 Fallback Strategy
text

Simple Query → Lite Tier
       │
       ▼
┌─────────────────────┐
│ Try: Gemini Flash    │──── Success ──→ Return response
│      Lite            │
└──────────┬──────────┘



☁️ Deployment (Streamlit Cloud)
Push code to GitHub
Go to share.streamlit.io
Connect your GitHub repo
Set app.py as main file
Add secrets in Advanced Settings:
toml

VERTEX_PROJECT_ID = "your-gcp-project-id"
VERTEX_LOCATION = "us-central1"
Deploy → Get shareable URL (requires GCP credentials)


🛠️ Tech Stack
Streamlit — UI Framework & real-time updates
Vertex AI Generative Models — All LLM execution
Google Cloud — Infrastructure & authentication
Pandas — Analytics & data processing
Plotly — Interactive charts & visualizations


🔮 Future Improvements
 Multi-turn conversation memory
 Additional agents (web search, summarizer, code executor)
 User feedback system (thumbs up/down)
 Query logging and analytics dashboard
 Authentication for access control
 A/B testing between model tiers
```
