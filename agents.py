"""
Sub-Agent Engine — Sophisticated prompts + automatic fallback.
Uses Vertex AI Generative Models for execution.
"""

import time
from vertexai.generative_models import GenerativeModel, GenerationConfig
from config import ALL_MODELS, TIER_MAX_OUTPUT_TOKENS


def _get_token_counts(response):
    """Safely extract token counts from Vertex AI response.
    
    Vertex AI generative_models.GenerativeModel returns usage_metadata with:
    - prompt_token_count: input tokens
    - candidates_token_count: output tokens (from response generation)
    """
    if not response or not response.usage_metadata:
        return 0, 0, 0
    
    try:
        usage = response.usage_metadata
        # Correct field names for Vertex AI SDK
        prompt_tokens = getattr(usage, 'prompt_token_count', 0)
        candidates_tokens = getattr(usage, 'candidates_token_count', 0)
        
        total_tokens = prompt_tokens + candidates_tokens
        return prompt_tokens, candidates_tokens, total_tokens
    except Exception as e:
        # If extraction fails, return 0 but log for debugging
        return 0, 0, 0

AGENT_PROMPTS = {
    "coding": """You are a senior software engineer with 10+ years of experience.

EVERY response must follow this structure:
1. **Problem Understanding** — restate in one line
2. **Approach** — explain your strategy in 2-3 bullets
3. **Solution** — complete, runnable code with:
   - Language-tagged code block
   - Type hints on functions
   - Docstring explaining purpose
   - Comments for non-obvious logic
   - Edge case handling
4. **Example Usage** — show how to use it
5. **Complexity** — Time: O(?), Space: O(?)

RULES: Never give partial code. Handle edge cases. State assumptions.""",

    "math": """You are an expert mathematician and patient tutor.

EVERY response must follow this structure:
1. **Problem Type** — classify it (algebra, calculus, proof, etc.)
2. **Given** — list known information
3. **Method** — state which formula/theorem you'll use
4. **Solution** — numbered steps, show EVERY calculation
5. **Verification** — check answer using different method
6. **Final Answer** — clearly highlighted

RULES: Never skip steps. Always verify. Show all arithmetic.""",

    "reasoning": """You are a senior analyst and strategic thinker.

EVERY response must follow this structure:
1. **Understanding** — restate the question
2. **Key Factors** — list important considerations
3. **Analysis** — structured exploration:
   - Comparisons → use a table
   - Explanations → use numbered steps
   - Decisions → list options with pros/cons
4. **Conclusion** — clear direct answer
5. **Recommendation** — actionable next steps

RULES: Be specific. Use tables for comparisons. Consider multiple angles.""",
}


def run_agent(query: str, agent_type: str, model_key: str) -> dict:
    """Execute agent with specified model. Auto-fallback on failure."""

    prompt = AGENT_PROMPTS.get(agent_type, AGENT_PROMPTS["reasoning"])

    if model_key not in ALL_MODELS:
        model_key = "standard_a"

    cfg = ALL_MODELS[model_key]
    error_msg = None
    fallback_used = False
    attempted = cfg["label"]

    full_prompt = f"{prompt}\n\nUser query: {query}"

    # Build fallback order: requested key -> same tier -> standard -> lite -> remaining.
    fallback_order = [model_key]
    tier = cfg["tier"]
    fallback_order.extend([k for k, v in ALL_MODELS.items() if v["tier"] == tier and k != model_key])
    fallback_order.extend(["standard_a", "lite_a"])
    fallback_order.extend(ALL_MODELS.keys())

    # Deduplicate while preserving order.
    deduped_keys = []
    for key in fallback_order:
        if key in ALL_MODELS and key not in deduped_keys:
            deduped_keys.append(key)

    response = None
    latency = 0.0
    errors = []
    for idx, key in enumerate(deduped_keys):
        try:
            start = time.time()
            candidate_cfg = ALL_MODELS[key]
            tier_max_output_tokens = TIER_MAX_OUTPUT_TOKENS.get(candidate_cfg["tier"], 4096)
            gen_config = GenerationConfig(
                temperature=0.3,
                max_output_tokens=tier_max_output_tokens,
            )
            model = GenerativeModel(candidate_cfg["model"])
            response = model.generate_content(
                contents=full_prompt,
                generation_config=gen_config,
            )
            latency = (time.time() - start) * 1000
            cfg = candidate_cfg
            model_key = key
            fallback_used = idx > 0
            break
        except Exception as e:
            errors.append(f"{key}: {str(e)}")

    if response is None:
        # Last-resort controlled response to avoid crashing the app.
        fallback_used = True
        error_msg = " | ".join(errors)[:1000] if errors else "Unknown model execution error"
        return {
            "response": "I could not generate a response because no configured Vertex AI models are currently accessible for this project.",
            "model_used": cfg["model"],
            "model_label": cfg["label"],
            "model_key": model_key,
            "tier": cfg["tier"],
            "provider": cfg["provider"],
            "agent": agent_type,
            "latency_ms": 0.0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0,
            "fallback_used": fallback_used,
            "attempted_model": attempted,
            "error": error_msg,
        }

    error_msg = " | ".join(errors)[:1000] if errors else None

    # Extract usage information
    prompt_tokens, completion_tokens, total_tokens = _get_token_counts(response)
    
    cost = (total_tokens / 1000) * cfg["cost_per_1k_tokens"]

    return {
        "response": response.text,
        "model_used": cfg["model"],
        "model_label": cfg["label"],
        "model_key": model_key,
        "tier": cfg["tier"],
        "provider": cfg["provider"],
        "agent": agent_type,
        "latency_ms": round(latency, 1),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "estimated_cost": cost,
        "fallback_used": fallback_used,
        "attempted_model": attempted,
        "error": error_msg,
    }