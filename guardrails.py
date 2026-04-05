"""
Three-layer guardrail system for safety and cost control.

Layer 1: INPUT  — Block bad queries before LLM call (injection, PII, rate limit)
Layer 2: OUTPUT — Scan responses after LLM call (safety, quality)
Layer 3: SYSTEM — Cost ceiling and daily budget enforcement
"""

import re
import time
import datetime
from config import GUARDRAIL_CONFIG

_request_timestamps = []
_daily_cost = 0.0
_daily_reset = datetime.date.today()


def check_input(query: str) -> dict:
    """Layer 1: Validate user input before LLM processing.
    
    Checks:
    - Length: Truncate if exceeds max_query_length (5000 chars)
    - Prompt Injection: Block if contains jailbreak phrases
    - PII: Detect email, phone, SSN, credit card and warn user
    - Rate Limit: Block if > max requests per minute (20 req/min)
    
    Returns:
        {"ok": bool, "clean_query": str, "warnings": [str], "reason": str|None}
    """
    warnings = []
    clean = query.strip()

    if not clean:
        return {"ok": False, "reason": "Please enter a query.", "warnings": [], "clean_query": ""}

    # Length
    max_len = GUARDRAIL_CONFIG["max_query_length"]
    if len(clean) > max_len:
        clean = clean[:max_len]
        warnings.append(f"Query truncated to {max_len} characters.")

    # Prompt injection
    q_lower = clean.lower()
    for phrase in GUARDRAIL_CONFIG["blocked_phrases"]:
        if phrase in q_lower:
            return {
                "ok": False,
                "reason": f"🛡️ **Prompt injection detected**\n\nBlocked pattern: `{phrase}`\n\nThis safety mechanism prevents prompt manipulation attacks.",
                "warnings": [],
                "clean_query": clean,
            }

    # PII detection
    for pii_type, pattern in GUARDRAIL_CONFIG["pii_patterns"].items():
        if re.search(pattern, clean):
            warnings.append(f"⚠️ Possible **{pii_type}** detected. AI models may log inputs — consider removing personal data.")

    # Rate limit
    global _request_timestamps
    now = time.time()
    _request_timestamps = [t for t in _request_timestamps if now - t < 60]
    limit = GUARDRAIL_CONFIG["rate_limit_per_minute"]
    if len(_request_timestamps) >= limit:
        return {
            "ok": False,
            "reason": f"🚦 Rate limit: max {limit} queries/minute. Please wait.",
            "warnings": [],
            "clean_query": clean,
        }
    _request_timestamps.append(now)

    return {"ok": True, "reason": None, "warnings": warnings, "clean_query": clean}


def check_output(response: str, agent_type: str) -> list:
    """Layer 2: Scan LLM response for safety & quality issues.
    
    Checks:
    - Min Length: Warn if response too short (< 10 chars)
    - Dangerous Code: Flag dangerous patterns if coding agent (os.system, eval, DROP TABLE)
    - Uncertainty: Detect if model expressed doubt ("not sure", "cannot verify")
    
    Returns:
        List of warning messages (empty if no issues)
    """
    warnings = []

    if not response or len(response.strip()) < GUARDRAIL_CONFIG["min_response_length"]:
        warnings.append("⚠️ Response is very short. Consider upgrading to a more powerful model.")

    # Dangerous code
    if agent_type == "coding":
        found = [p for p in GUARDRAIL_CONFIG["dangerous_code_patterns"] if p.lower() in response.lower()]
        if found:
            warnings.append(f"⚠️ **Potentially dangerous code:** `{'`, `'.join(found)}` — review before running.")

    # Uncertainty
    for phrase in ["i'm not sure", "i cannot verify", "i don't have access", "this may be incorrect"]:
        if phrase in response.lower():
            warnings.append("ℹ️ Model expressed uncertainty. Consider upgrading for a more confident answer.")
            break

    return warnings


def track_cost(cost: float) -> dict:
    """Layer 3: Track daily API cost and enforce ceiling.
    
    Accumulates cost per day, resets at midnight UTC.
    Alerts user if daily_cost exceeds ceiling ($5/day).
    
    Returns:
        {"daily_total": float, "ceiling": float, "exceeded": bool, ...}
    """
    global _daily_cost, _daily_reset
    today = datetime.date.today()
    if today != _daily_reset:
        _daily_cost = 0.0
        _daily_reset = today
    _daily_cost += cost
    ceiling = GUARDRAIL_CONFIG["daily_cost_ceiling"]
    return {
        "daily_total": round(_daily_cost, 6),
        "ceiling": ceiling,
        "remaining": round(ceiling - _daily_cost, 6),
        "pct": round((_daily_cost / ceiling) * 100, 2),
        "exceeded": _daily_cost > ceiling,
    }


def get_status() -> dict:
    """Get current system status for sidebar."""
    now = time.time()
    recent = len([t for t in _request_timestamps if now - t < 60])
    limit = GUARDRAIL_CONFIG["rate_limit_per_minute"]
    ceiling = GUARDRAIL_CONFIG["daily_cost_ceiling"]
    return {
        "req_per_min": recent,
        "rate_limit": limit,
        "rate_pct": round((recent / limit) * 100, 1),
        "daily_cost": round(_daily_cost, 6),
        "ceiling": ceiling,
        "cost_pct": round((_daily_cost / ceiling) * 100, 2),
    }
