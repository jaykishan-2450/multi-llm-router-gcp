import os

# These will be read from Streamlit Secrets in deployment
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# If running on Streamlit Cloud, secrets are accessed differently
try:
    import streamlit as st
    if hasattr(st, "secrets"):
        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", GROQ_API_KEY)
        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", GEMINI_API_KEY)
except Exception:
    pass

MODELS = {
    "pro": {
        "model": "groq/llama-3.3-70b-versatile",
        "api_key": GROQ_API_KEY,
        "label": "Pro (70B)",
        "cost_per_1k_tokens": 0.0008,
        "avg_latency_ms": 3000,
    },
    "standard": {
        "model": "groq/llama-3.1-8b-instant",
        "api_key": GROQ_API_KEY,
        "label": "Standard (8B)",
        "cost_per_1k_tokens": 0.0001,
        "avg_latency_ms": 800,
    },
    "lite": {
        "primary": {
            "model": "gemini/gemini-2.0-flash-lite",
            "api_key": GEMINI_API_KEY,
            "label": "Lite (Gemini Flash-Lite)",
            "cost_per_1k_tokens": 0.00005,
            "avg_latency_ms": 400,
        },
        "fallback": {
            "model": "groq/llama-3.1-8b-instant",
            "api_key": GROQ_API_KEY,
            "label": "Lite Fallback (Groq 8B)",
            "cost_per_1k_tokens": 0.0001,
            "avg_latency_ms": 800,
        },
        "model": "gemini/gemini-2.0-flash-lite",
        "api_key": GEMINI_API_KEY,
        "label": "Lite (Gemini Flash-Lite)",
        "cost_per_1k_tokens": 0.00005,
        "avg_latency_ms": 400,
    },
}

ROUTER_MODEL = {
    "model": "groq/llama-3.1-8b-instant",
    "api_key": GROQ_API_KEY,
}

AGENT_TYPES = ["coding", "reasoning", "math"]