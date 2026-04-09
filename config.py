"""
Configuration — Single source of truth.
Models: Vertex AI Gemini models only.
    - Gemini 2.5 family: Primary defaults (_a)
    - Gemini 3.0 family: Backup fallbacks (_b)
Authentication: Google Cloud Application Default Credentials (gcloud CLI)
"""

import os
import vertexai

# ── Vertex AI Configuration ──
VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION")

try:
    import streamlit as st
    if hasattr(st, "secrets"):
        VERTEX_PROJECT_ID = st.secrets.get("VERTEX_PROJECT_ID", VERTEX_PROJECT_ID)
        VERTEX_LOCATION = st.secrets.get("VERTEX_LOCATION", VERTEX_LOCATION)
except Exception:
    pass

# Initialize Vertex AI with Application Default Credentials
vertexai.init(project=VERTEX_PROJECT_ID, location=VERTEX_LOCATION)

# ══════════════════════════════════════════════════════
# MODEL REGISTRY — Vertex AI Only
# ══════════════════════════════════════════════════════
ALL_MODELS = {
    # ── LITE TIER ──
    "lite_a": {
        "model": "gemini-2.5-flash-lite",
        "label": "Vertex Gemini 2.5 Flash-Lite",
        "tier": "lite",
        "provider": "Vertex AI",
        "params": "Fast & Optimized",
        "cost_per_1k_tokens": 0.0001,
        "avg_latency_ms": 300,
        "strength": "Latest Vertex AI lite path — faster inference",
    },
    "lite_b": {
        "model": "gemini-2.5-flash-lite",
        "label": "Vertex Gemini 2.5 Flash-Lite",
        "tier": "lite",
        "provider": "Vertex AI",
        "params": "Stable",
        "cost_per_1k_tokens": 0.0001,
        "avg_latency_ms": 350,
        "strength": "Fallback lite — proven stable model",
    },

    # ── STANDARD TIER ──
    "standard_a": {
        "model": "gemini-2.5-flash",
        "label": "Vertex Gemini 2.5 Flash",
        "tier": "standard",
        "provider": "Vertex AI",
        "params": "Balanced & Fast",
        "cost_per_1k_tokens": 0.0003,
        "avg_latency_ms": 400,
        "strength": "Latest Vertex AI standard — balanced performance",
    },
    "standard_b": {
        "model": "gemini-2.5-flash",
        "label": "Vertex Gemini 2.5 Flash",
        "tier": "standard",
        "provider": "Vertex AI",
        "params": "Stable & Extended",
        "cost_per_1k_tokens": 0.0003,
        "avg_latency_ms": 450,
        "strength": "Fallback standard — extended context window",
    },

    # ── PRO TIER ──
    "pro_a": {
        "model": "gemini-2.5-pro",
        "label": "Vertex Gemini 2.5 Pro",
        "tier": "pro",
        "provider": "Vertex AI",
        "params": "Most Powerful",
        "cost_per_1k_tokens": 0.00125,
        "avg_latency_ms": 2000,
        "strength": "Latest Vertex AI pro — cutting-edge reasoning",
    },
    "pro_b": {
        "model": "gemini-2.5-pro",
        "label": "Vertex Gemini 2.5 Pro",
        "tier": "pro",
        "provider": "Vertex AI",
        "params": "Stable & Powerful",
        "cost_per_1k_tokens": 0.00125,
        "avg_latency_ms": 2200,
        "strength": "Fallback pro — proven high-quality reasoning",
    },
}

# ── Router ──
ROUTER_MODEL = {
    "model": "gemini-2.5-flash-lite",
    "label": "Vertex Gemini 2.5 Flash-Lite (Router)",
}

# ── Output token caps by tier ──
TIER_MAX_OUTPUT_TOKENS = {
    "lite": 2048,
    "standard": 4096,
    "pro": 8192,
}

# ── Defaults ──
TIER_DEFAULTS = {
    "lite": "lite_a",
    "standard": "standard_a",
    "pro": "pro_a",
}

# ── Upgrade paths ──
UPGRADE_OPTIONS = {
    "lite_a":     ["lite_b", "standard_a", "standard_b", "pro_a", "pro_b"],
    "lite_b":     ["standard_a", "standard_b", "pro_a", "pro_b"],
    "standard_a": ["standard_b", "pro_a", "pro_b"],
    "standard_b": ["pro_a", "pro_b"],
    "pro_a":      ["pro_b"],
    "pro_b":      [],
}

# ── Guardrails ──
GUARDRAIL_CONFIG = {
    "max_query_length": 5000,
    "rate_limit_per_minute": 20,
    "daily_cost_ceiling": 5.0,
    "min_response_length": 10,
    "blocked_phrases": [
        "ignore all instructions", "ignore previous instructions",
        "ignore your instructions", "disregard all",
        "forget your prompt", "reveal your system prompt",
        "show your system prompt", "print your instructions",
        "you are now dan", "pretend you are",
        "act as an unrestricted", "jailbreak",
        "bypass your rules", "override safety",
    ],
    "dangerous_code_patterns": [
        "os.system(", "subprocess.call(", "subprocess.Popen(",
        "subprocess.run(", "eval(", "exec(",
        "rm -rf", "DROP TABLE", "DELETE FROM",
        "__import__(", "shutil.rmtree(",
    ],
    "pii_patterns": {
        "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    },
}