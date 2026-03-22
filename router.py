import json
import time
import litellm
from config import ROUTER_MODEL, MODELS

litellm.drop_params = True

ROUTER_SYSTEM_PROMPT = """You are a query router for a multi-agent AI system.

Given a user query, you must output ONLY valid JSON (no markdown, no explanation) with exactly these fields:

{
  "agent": "<coding|reasoning|math>",
  "complexity": "<simple|medium|complex>",
  "reason": "<one line explanation>"
}

RULES:
- "coding" → programming, code generation, debugging, algorithms, data structures
- "math" → calculations, equations, proofs, statistics, linear algebra
- "reasoning" → logic, analysis, comparisons, planning, general knowledge

COMPLEXITY:
- "simple" → trivial tasks (add two numbers, print hello world, basic facts)
- "medium" → moderate tasks (sort algorithm, solve quadratic, compare concepts)
- "complex" → hard tasks (system design, proofs, optimize code, multi-step reasoning)

Output ONLY the JSON object. Nothing else."""


def route_query(query: str) -> dict:
    """Classify query into agent type + complexity tier. Returns routing info + latency."""
    start = time.time()

    response = litellm.completion(
        model=ROUTER_MODEL["model"],
        api_key=ROUTER_MODEL["api_key"],
        messages=[
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0,
        max_tokens=150,
    )

    routing_latency = (time.time() - start) * 1000  # ms

    raw = response.choices[0].message.content.strip()
    # Clean markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"agent": "reasoning", "complexity": "medium", "reason": "Failed to parse, defaulting"}

    # Map complexity to model tier
    complexity_to_tier = {
        "simple": "lite",
        "medium": "standard",
        "complex": "pro",
    }
    tier = complexity_to_tier.get(result.get("complexity", "medium"), "standard")
    model_config = MODELS[tier]

    return {
        "agent": result.get("agent", "reasoning"),
        "complexity": result.get("complexity", "medium"),
        "reason": result.get("reason", ""),
        "tier": tier,
        "model": model_config["model"],
        "model_label": model_config["label"],
        "routing_latency_ms": round(routing_latency, 1),
        "router_tokens": response.usage.total_tokens if response.usage else 0,
    }