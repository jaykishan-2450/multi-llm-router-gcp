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
           │      🧠 DEEP AGENT (Router)   │
           │    groq/llama-3.1-8b-instant   │
           │                               │
           │  Classifies:                  │
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
     │ 🟢 Simple  → Gemini Flash-Lite       │
     │              (fallback: Groq 8B)     │
     │ 🟠 Medium  → Groq LLaMA 8B          │
     │ 🔴 Complex → Groq LLaMA 70B         │
     └──────────────────────────────────────┘
                    │
                    ▼
     ┌──────────────────────────────────────┐
     │  📊 Response + Metrics + Comparison  │
     └──────────────────────────────────────┘

---

## ✨ Key Features

- **🤖 Intelligent Routing** — Deep Agent classifies every query and picks the right sub-agent + model automatically
- **💰 Cost Optimization** — Simple tasks use cheap models, complex tasks get powerful models
- **⚡ Dynamic Model Selection** — Model tier decided at runtime, not hardcoded
- **🔄 Fallback Strategy** — If Gemini fails (rate limit), automatically falls back to Groq with error visibility
- **📊 Full Observability** — Latency, token usage, cost comparison shown for every query
- **🎯 3 Specialized Agents** — Coding, Reasoning, and Math each with optimized system prompts

---

## 📊 Model Tiers

| Tier                 | Model                          | Use Case                                | Cost    |
| -------------------- | ------------------------------ | --------------------------------------- | ------- |
| 🟢 **Lite**          | `gemini/gemini-2.0-flash-lite` | Simple tasks (add numbers, basic facts) | Lowest  |
| 🟢 **Lite Fallback** | `groq/llama-3.1-8b-instant`    | When Gemini rate-limited                | Low     |
| 🟠 **Standard**      | `groq/llama-3.1-8b-instant`    | Medium tasks (algorithms, comparisons)  | Medium  |
| 🔴 **Pro**           | `groq/llama-3.3-70b-versatile` | Complex tasks (system design, proofs)   | Highest |
| 🔧 **Router**        | `groq/llama-3.1-8b-instant`    | Query classification only               | Minimal |

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
4. Set API Keys
Bash

# Windows PowerShell
$env:GROQ_API_KEY = "gsk_your_groq_key_here"
$env:GEMINI_API_KEY = "your_gemini_key_here"

# Mac/Linux
export GROQ_API_KEY="gsk_your_groq_key_here"
export GEMINI_API_KEY="your_gemini_key_here"
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
│ Model          │ Cost     │ Latency  │
├────────────────┼──────────┼──────────┤
│ 🔴 Pro (70B)   │ $0.00010 │ ~3000ms  │
│ 🟠 Std (8B)    │ $0.00001 │ ~800ms   │
│ 🟢 Lite        │ $0.00001 │ ~400ms   │ ← Selected
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
           │
       Rate Limit / Error
           │
           ▼
┌─────────────────────┐
│ Fallback: Groq 8B   │──── Success ──→ Return response
│                      │                 + Error displayed in UI
└─────────────────────┘
☁️ Deployment (Streamlit Cloud)
Push code to GitHub
Go to share.streamlit.io
Connect your GitHub repo
Set app.py as main file
Add secrets in Advanced Settings:
toml

GROQ_API_KEY = "gsk_your_key"
GEMINI_API_KEY = "your_key"
Deploy → Get shareable URL
🛠️ Tech Stack
Streamlit — UI Framework
LiteLLM — Unified LLM API (100+ providers)
Groq — Ultra-fast LLM inference (LLaMA models)
Google Gemini — Gemini Flash-Lite for lightweight tasks
🔮 Future Improvements
 Multi-turn conversation memory
 Additional agents (web search, summarizer, code executor)
 User feedback system (thumbs up/down)
 Query logging and analytics dashboard
 Authentication for access control
 A/B testing between model tiers
