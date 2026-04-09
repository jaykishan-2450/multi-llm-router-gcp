"""
Logprobs Extractor — Extract logprobs from Vertex AI and calculate confidence.
Uses response_logprobs=True to get token-level log probabilities.
Logs results to logprobs_analysis.csv for validation.
"""

import json
import csv
import time
import math
import os
import vertexai
from datetime import datetime
from vertexai.generative_models import GenerativeModel, GenerationConfig

# ── Vertex AI Configuration (same pattern as config.py) ──
VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION")

try:
    import streamlit as st
    if hasattr(st, "secrets"):
        VERTEX_PROJECT_ID = st.secrets.get("VERTEX_PROJECT_ID", VERTEX_PROJECT_ID)
        VERTEX_LOCATION = st.secrets.get("VERTEX_LOCATION", VERTEX_LOCATION)
except Exception:
    pass

vertexai.init(project=VERTEX_PROJECT_ID, location=VERTEX_LOCATION)

ROUTER_MODEL = {
    "model": os.getenv("ROUTER_MODEL", "gemini-2.5-flash-lite"),
    "label": "Vertex Gemini 2.5 Flash-Lite (Router)",
}

TIER_TO_MODEL_LABEL = {
    "lite": "Vertex Gemini 2.5 Flash-Lite",
    "standard": "Vertex Gemini 2.5 Flash",
    "pro": "Vertex Gemini 2.5 Pro",
}

ROUTER_PROMPT = """You are a query classifier for a multi-agent AI system.

OUTPUT: Only valid JSON, nothing else.
{
  "agent": "<coding|reasoning|math>",
  "complexity": "<simple|medium|complex>",
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

Output ONLY the JSON."""


def _calculate_confidence_from_logprobs(logprobs_result) -> dict:
    """
    Extract confidence metrics from logprobs_result.
    
    Returns:
        {
            "top_logprob": float,
            "margin": float (top1 - top2),
            "entropy": float,
            "confidence_score": float (0.0-1.0)
        }
    """
    if not logprobs_result or not hasattr(logprobs_result, 'token_logprobs'):
        return {"top_logprob": 0.0, "margin": 0.0, "entropy": 0.0, "confidence_score": 0.5}
    
    try:
        token_logprobs = logprobs_result.token_logprobs
        
        if not token_logprobs or len(token_logprobs) == 0:
            return {"top_logprob": 0.0, "margin": 0.0, "entropy": 0.0, "confidence_score": 0.5}
        
        # Use first token logprobs as the decision point
        first_token = token_logprobs[0]
        
        # Extract logprobs for each candidate
        candidates = []
        if hasattr(first_token, 'candidates'):
            for candidate in first_token.candidates:
                logprob = candidate.log_probability if hasattr(candidate, 'log_probability') else 0.0
                candidates.append(logprob)
        
        if len(candidates) < 2:
            return {"top_logprob": candidates[0] if candidates else 0.0, "margin": 0.0, "entropy": 0.0, "confidence_score": 0.5}
        
        # Sort candidates (highest logprob first)
        candidates_sorted = sorted(candidates, reverse=True)
        top_logprob = candidates_sorted[0]
        second_logprob = candidates_sorted[1]
        
        # Margin: difference between top 2 (higher = more confident)
        margin = top_logprob - second_logprob
        
        # Convert logprobs to probabilities using softmax
        exp_logprobs = [math.exp(lp) for lp in candidates_sorted]
        sum_exp = sum(exp_logprobs)
        probs = [e / sum_exp for e in exp_logprobs]
        
        # Entropy: -sum(p * log(p)) (lower = more confident)
        entropy = -sum(p * math.log(p) for p in probs if p > 0)
        max_entropy = math.log(len(probs))  # Normalize by max possible entropy
        entropy_normalized = entropy / max_entropy if max_entropy > 0 else 0.5
        
        # Combined confidence: margin + (1 - normalized entropy)
        confidence_score = min(1.0, (margin + 1.0) / 2.0 * (1.0 - entropy_normalized * 0.3))
        confidence_score = max(0.3, min(1.0, confidence_score))
        
        return {
            "top_logprob": round(top_logprob, 4),
            "margin": round(margin, 4),
            "entropy": round(entropy_normalized, 4),
            "confidence_score": round(confidence_score, 4)
        }
    
    except Exception as e:
        print(f"Error calculating confidence: {e}")
        return {"top_logprob": 0.0, "margin": 0.0, "entropy": 0.0, "confidence_score": 0.5}


def route_query_with_logprobs(query: str) -> dict:
    """
    Classify query using Vertex AI with logprobs enabled.
    Returns classification + logprob-based confidence.
    """
    start = time.time()
    full_prompt = f"{ROUTER_PROMPT}\n\nUser query: {query}"
    
    logprobs_metrics = {"top_logprob": 0.0, "margin": 0.0, "entropy": 0.0, "confidence_score": 0.5}
    parsed = None
    
    try:
        model = GenerativeModel(ROUTER_MODEL["model"])
        
        # ✅ Enable logprobs in generation config
        response = model.generate_content(
            contents=full_prompt,
            generation_config=GenerationConfig(
                temperature=0.0,
                max_output_tokens=200,
                response_logprobs=True,  # ← Enable logprobs
                logprobs=5                # ← Return top-5 alternative tokens
            ),
        )
        
        # Extract response text
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        
        parsed = json.loads(raw)
        
        # Extract logprobs from response
        if response and hasattr(response, 'candidates') and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, 'logprobs_result'):
                logprobs_metrics = _calculate_confidence_from_logprobs(candidate.logprobs_result)
    
    except Exception as e:
        parsed = {
            "agent": "reasoning",
            "complexity": "medium",
            "reason": f"Router error: {str(e)[:100]}"
        }
    
    latency = (time.time() - start) * 1000
    
    # Extract and validate classification
    agent = parsed.get("agent", "reasoning")
    if agent not in ("coding", "math", "reasoning"):
        agent = "reasoning"
    
    complexity = parsed.get("complexity", "medium")
    if complexity not in ("simple", "medium", "complex"):
        complexity = "medium"
    
    # Use logprob-based confidence, not self-reported
    confidence = logprobs_metrics["confidence_score"]
    
    tier = {"simple": "lite", "medium": "standard", "complex": "pro"}[complexity]
    model_label = TIER_TO_MODEL_LABEL[tier]
    
    return {
        "query": query,
        "agent": agent,
        "complexity": complexity,
        "confidence": confidence,
        "reason": parsed.get("reason", ""),
        "tier": tier,
        "model_label": model_label,
        "routing_latency_ms": round(latency, 1),
        # Logprobs metrics
        "logprob_top": logprobs_metrics["top_logprob"],
        "logprob_margin": logprobs_metrics["margin"],
        "logprob_entropy": logprobs_metrics["entropy"],
    }


def log_to_csv(results: list, filename: str = "logprobs_analysis.csv"):
    """Log routing + logprobs results to CSV."""
    if not results:
        return
    
    fieldnames = [
        "timestamp", "query", "agent", "complexity", "confidence",
        "logprob_top", "logprob_margin", "logprob_entropy",
        "tier", "routing_latency_ms", "reason"
    ]
    
    try:
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            # Write header if file is empty
            f.seek(0, 2)  # Seek to end
            if f.tell() == 0:
                writer.writeheader()
            
            for result in results:
                row = {
                    "timestamp": datetime.now().isoformat(),
                    "query": result.get("query", ""),
                    "agent": result.get("agent", ""),
                    "complexity": result.get("complexity", ""),
                    "confidence": result.get("confidence", 0.0),
                    "logprob_top": result.get("logprob_top", 0.0),
                    "logprob_margin": result.get("logprob_margin", 0.0),
                    "logprob_entropy": result.get("logprob_entropy", 0.0),
                    "tier": result.get("tier", ""),
                    "routing_latency_ms": result.get("routing_latency_ms", 0),
                    "reason": result.get("reason", "")
                }
                writer.writerow(row)
        print(f"✅ Logged {len(results)} results to {filename}")
    except Exception as e:
        print(f"❌ Error writing CSV: {e}")


def test_logprobs(test_queries: list = None):
    """Test logprobs extraction with sample queries."""
    if test_queries is None:
        test_queries = [
            "What is 25 * 48?",
            "Write a Python function to check if a number is prime",
            "Design a thread-safe LRU cache",
            "Compare SQL vs NoSQL for ecommerce",
            "Capital of France?",
        ]
    
    results = []
    print(f"\n🧪 Testing logprobs extraction with {len(test_queries)} queries...\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"[{i}/{len(test_queries)}] Processing: {query[:50]}...")
        result = route_query_with_logprobs(query)
        results.append(result)
        
        print(f"  → Agent: {result['agent']}")
        print(f"  → Complexity: {result['complexity']}")
        print(f"  → Confidence (logprobs): {result['confidence']:.3f}")
        print(f"  → Margin: {result['logprob_margin']:.4f}, Entropy: {result['logprob_entropy']:.4f}")
        print()
    
    # Log all results to CSV
    log_to_csv(results)
    return results


if __name__ == "__main__":
    print(f"Using Vertex project: {VERTEX_PROJECT_ID}, location: {VERTEX_LOCATION}")
    print(f"Router model: {ROUTER_MODEL['model']}")

    # Run test suite
    results = test_logprobs()
    
    print("\n" + "="*60)
    print("✅ Logprobs extraction complete!")
    print("📊 Results saved to: logprobs_analysis.csv")
    print("="*60)