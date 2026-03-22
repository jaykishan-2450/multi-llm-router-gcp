import time
import litellm
import streamlit as st
from config import MODELS

litellm.drop_params = True

AGENT_SYSTEM_PROMPTS = {
    "coding": """You are an expert coding assistant. You write clean, correct, well-commented code.
Always provide the solution in proper code blocks with the language specified.
If debugging, explain the bug and the fix clearly.""",

    "reasoning": """You are an expert reasoning and analysis assistant.
Think step by step. Be logical, structured, and thorough.
Use bullet points and clear structure in your answers.""",

    "math": """You are an expert math assistant. Solve problems step by step.
Show all work clearly. Use proper mathematical notation where possible.
Double-check your calculations before presenting the final answer.""",
}


def _call_llm(model: str, api_key: str, system_prompt: str, query: str):
    """Single LLM call, returns (response, latency_ms)."""
    start = time.time()
    response = litellm.completion(
        model=model,
        api_key=api_key,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
        temperature=0.3,
        max_tokens=2048,
    )
    latency = (time.time() - start) * 1000
    return response, latency


def run_agent(query: str, agent_type: str, tier: str) -> dict:
    """Execute sub-agent with dynamic model. For lite tier, try Gemini first then fallback to Groq."""

    system_prompt = AGENT_SYSTEM_PROMPTS.get(agent_type, AGENT_SYSTEM_PROMPTS["reasoning"])
    fallback_used = False
    gemini_error = None

    if tier == "lite":
        # ── Try Gemini primary first ──
        primary = MODELS["lite"]["primary"]
        try:
            response, agent_latency = _call_llm(
                primary["model"], primary["api_key"], system_prompt, query
            )
            model_used = primary["model"]
            model_label = primary["label"]
            cost_rate = primary["cost_per_1k_tokens"]

        except Exception as e:
            # ── Capture the ACTUAL error ──
            gemini_error = str(e)
            fallback_used = True

            fallback = MODELS["lite"]["fallback"]
            response, agent_latency = _call_llm(
                fallback["model"], fallback["api_key"], system_prompt, query
            )
            model_used = fallback["model"]
            model_label = fallback["label"] + " ⚠️"
            cost_rate = fallback["cost_per_1k_tokens"]

    else:
        model_config = MODELS[tier]
        response, agent_latency = _call_llm(
            model_config["model"], model_config["api_key"], system_prompt, query
        )
        model_used = model_config["model"]
        model_label = model_config["label"]
        cost_rate = model_config["cost_per_1k_tokens"]

    total_tokens = response.usage.total_tokens if response.usage else 0
    prompt_tokens = response.usage.prompt_tokens if response.usage else 0
    completion_tokens = response.usage.completion_tokens if response.usage else 0
    estimated_cost = (total_tokens / 1000) * cost_rate

    return {
        "response": response.choices[0].message.content,
        "model_used": model_used,
        "model_label": model_label,
        "tier": tier,
        "agent": agent_type,
        "latency_ms": round(agent_latency, 1),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "estimated_cost": estimated_cost,
        "fallback_used": fallback_used,
        "gemini_error": gemini_error,
    }


def compute_comparison(actual_result: dict) -> list:
    """Show what it WOULD have cost/taken if we used every tier."""
    comparisons = []

    for tier_name in ["pro", "standard"]:
        cfg = MODELS[tier_name]
        token_count = actual_result["total_tokens"]
        est_cost = (token_count / 1000) * cfg["cost_per_1k_tokens"]
        comparisons.append({
            "tier": tier_name,
            "label": cfg["label"],
            "model": cfg["model"],
            "est_cost": est_cost,
            "avg_latency_ms": cfg["avg_latency_ms"],
            "was_selected": tier_name == actual_result["tier"],
        })

    lite_primary = MODELS["lite"]["primary"]
    lite_fallback = MODELS["lite"]["fallback"]

    if actual_result.get("fallback_used"):
        lite_cfg = lite_fallback
    else:
        lite_cfg = lite_primary

    token_count = actual_result["total_tokens"]
    est_cost = (token_count / 1000) * lite_cfg["cost_per_1k_tokens"]
    comparisons.append({
        "tier": "lite",
        "label": lite_cfg["label"],
        "model": lite_cfg["model"],
        "est_cost": est_cost,
        "avg_latency_ms": lite_cfg["avg_latency_ms"],
        "was_selected": actual_result["tier"] == "lite",
    })

    return comparisons