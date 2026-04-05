"""
Query Router — Classifies queries into agent type + complexity.
Uses Vertex AI Gemini 2.5 Flash for fast, reliable routing.
"""

import json
import time
from vertexai.generative_models import GenerativeModel
from config import ROUTER_MODEL

def _get_total_tokens(response):
    """Safely extract total tokens from Vertex AI response.
    
    Vertex AI generative_models.GenerativeModel returns usage_metadata with:
    - prompt_tokens: input tokens
    - candidates_tokens: output tokens (from response generation)
    """
    if not response or not response.usage_metadata:
        return 0
    
    try:
        usage = response.usage_metadata
        # Vertex AI SDK uses these field names
        prompt_tokens = getattr(usage, 'prompt_tokens', None) or 0
        candidates_tokens = getattr(usage, 'candidates_tokens', None) or 0
        
        # Fallback field names if SDK changes
        if prompt_tokens == 0:
            prompt_tokens = getattr(usage, 'input_tokens', None) or 0
        if candidates_tokens == 0:
            candidates_tokens = getattr(usage, 'output_tokens', None) or 0
        
        return prompt_tokens + candidates_tokens
    except Exception as e:
        # If extraction fails, return 0
        return 0
ROUTER_PROMPT = """You are a query classifier for a multi-agent AI system.

OUTPUT: Only valid JSON, nothing else.
{
  "agent": "<coding|reasoning|math>",
  "complexity": "<simple|medium|complex>",
  "confidence": <0.0 to 1.0>,
  "reason": "<brief explanation>"
}

AGENT RULES:
- coding → needs CODE output (write/debug/implement code, SQL, scripts, algorithms)
- math → needs MATH work (calculations, equations, proofs, statistics)
- reasoning → needs ANALYSIS (comparisons, explanations, planning, facts, logic)

COMPLEXITY:
- simple → one-step obvious answer ("2+2", "hello world", "capital of France")
- medium → multi-step standard task ("binary search", "quadratic equation", "X vs Y")
- complex → deep expertise needed ("system design", "proofs", "architecture decisions")

EDGE CASES:
- "explain quicksort" → reasoning (wants explanation)
- "implement quicksort" → coding (wants code)
- Unsure about complexity → default "medium"
- Unsure about agent → default "reasoning"

Output ONLY the JSON."""


def route_query(query: str) -> dict:
    """Classify query into agent type and complexity tier using Vertex AI."""
    start = time.time()

    # Combine system prompt and user query into single message
    full_prompt = f"{ROUTER_PROMPT}\n\nUser query: {query}"

    parsed = None
    router_tokens = 0
    try:
        model = GenerativeModel(ROUTER_MODEL["model"])
        response = model.generate_content(
            contents=full_prompt,
            generation_config={
                "temperature": 0.0,
                "max_output_tokens": 200,
            },
        )
        router_tokens = _get_total_tokens(response)
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        parsed = json.loads(raw)
    except Exception as e:
        # Graceful fallback to keep the UI responsive if routing model is unavailable.
        parsed = {
            "agent": "reasoning",
            "complexity": "medium",
            "confidence": 0.2,
            "reason": f"Router fallback due to model error: {str(e)[:140]}",
        }

    latency = (time.time() - start) * 1000

    agent = parsed.get("agent", "reasoning")
    if agent not in ("coding", "math", "reasoning"):
        agent = "reasoning"

    complexity = parsed.get("complexity", "medium")
    if complexity not in ("simple", "medium", "complex"):
        complexity = "medium"

    confidence = parsed.get("confidence", 0.5)
    try:
        confidence = max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        confidence = 0.5

    # Import here to avoid circular dependency
    from config import TIER_DEFAULTS, ALL_MODELS
    
    tier = {"simple": "lite", "medium": "standard", "complex": "pro"}[complexity]
    model_key = TIER_DEFAULTS[tier]
    model_cfg = ALL_MODELS[model_key]

    return {
        "agent": agent,
        "complexity": complexity,
        "confidence": confidence,
        "reason": parsed.get("reason", ""),
        "tier": tier,
        "model_key": model_key,
        "model": model_cfg["model"],
        "model_label": model_cfg["label"],
        "routing_latency_ms": round(latency, 1),
        "router_tokens": router_tokens,
    }