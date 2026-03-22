import streamlit as st
import pandas as pd
from router import route_query
from agents import run_agent, compute_comparison

st.set_page_config(page_title="Deep Agent - Multi-Agent Router", layout="wide", page_icon="🤖")

# ── Custom CSS ──
st.markdown("""
<style>
    .tier-pro { background: #FF6B6B; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; }
    .tier-standard { background: #FFA94D; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; }
    .tier-lite { background: #51CF66; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; }
    .agent-badge { background: #339AF0; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; }
    .metric-card {
        background: #f8f9fa; border-radius: 10px; padding: 15px;
        border-left: 4px solid #339AF0; margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ──
st.title("🤖 Deep Agent — Dynamic Multi-Agent Router")
st.markdown("""
**Architecture:** One **Deep Agent (Router)** classifies your query → selects the right **Sub-Agent** 
(Coding / Reasoning / Math) AND picks the optimal **model tier** (Pro / Standard / Lite) at runtime.
""")

# ── Sidebar ──
with st.sidebar:
    st.header("⚙️ System Info")
    st.markdown("""
    | Tier | Model | Use Case |
    |------|-------|----------|
    | 🔴 Pro | LLaMA 70B | Complex tasks |
    | 🟠 Standard | LLaMA 8B | Medium tasks |
    | 🟢 Lite | Gemini Flash-Lite | Simple tasks |
    """)
    st.divider()
    st.markdown("**Router Model:** LLaMA 3.1 8B (Groq)")
    st.divider()

    st.header("🧪 Try These Examples")
    examples = {
        "Simple Coding": "Write a Python function to add two numbers",
        "Complex Coding": "Design a rate limiter using token bucket algorithm in Python with async support",
        "Simple Math": "What is 25 * 4?",
        "Complex Math": "Prove that the square root of 2 is irrational",
        "Simple Reasoning": "What is the capital of France?",
        "Complex Reasoning": "Compare microservices vs monolithic architecture for a startup with 5 engineers",
    }
    for label, example in examples.items():
        if st.button(label, key=label, use_container_width=True):
            st.session_state["query_input"] = example

# ── Main Input ──
query = st.text_area(
    "Enter your query:",
    value=st.session_state.get("query_input", ""),
    height=100,
    placeholder="Ask anything — coding, math, or reasoning...",
)

if st.button("🚀 Run Deep Agent", type="primary", use_container_width=True) and query.strip():

    # ── Step 1: Route ──
    with st.status("🔍 Deep Agent is analyzing your query...", expanded=True) as status:
        st.write("**Step 1:** Classifying query (agent + complexity)...")
        routing = route_query(query)

        tier_colors = {"pro": "🔴", "standard": "🟠", "lite": "🟢"}
        agent_emoji = {"coding": "💻", "reasoning": "🧠", "math": "🔢"}

        st.write(f"**Agent:** {agent_emoji.get(routing['agent'], '🤖')} {routing['agent'].title()}")
        st.write(f"**Complexity:** {routing['complexity'].title()} → {tier_colors.get(routing['tier'], '')} **{routing['model_label']}**")
        st.write(f"**Reason:** {routing['reason']}")
        st.write(f"**Routing Latency:** {routing['routing_latency_ms']}ms")

        # ── Step 2: Execute ──
        st.write(f"**Step 2:** Running {routing['agent']} agent with {routing['model_label']}...")
        result = run_agent(query, routing["agent"], routing["tier"])

        status.update(label="✅ Complete!", state="complete", expanded=False)

    # ── Fallback Warning Banner with Error Details ──
    if result.get("fallback_used"):
        gemini_error = result.get("gemini_error", "Unknown error")

        # Classify the error for user-friendly message
        if "429" in gemini_error or "rate" in gemini_error.lower() or "quota" in gemini_error.lower():
            error_type = "🚦 Rate Limit / Quota Exceeded"
            error_tip = "Free tier limit reached. Wait a few minutes or upgrade to paid Gemini API."
        elif "api key" in gemini_error.lower() or "401" in gemini_error or "403" in gemini_error:
            error_type = "🔑 API Key Invalid"
            error_tip = "Check your GEMINI_API_KEY. It may be expired or incorrect."
        elif "not found" in gemini_error.lower() or "404" in gemini_error:
            error_type = "❌ Model Not Found"
            error_tip = "The model name may be wrong. Try gemini/gemini-2.0-flash or gemini/gemini-1.5-flash."
        elif "location" in gemini_error.lower() or "region" in gemini_error.lower():
            error_type = "🌍 Region Not Supported"
            error_tip = "Gemini API may not be available in your region. Use a VPN or stick with Groq."
        elif "billing" in gemini_error.lower():
            error_type = "💳 Billing Not Enabled"
            error_tip = "Enable billing in Google Cloud Console for Gemini API access."
        else:
            error_type = "⚠️ Unknown Error"
            error_tip = "Check the raw error below for details."

        # Main warning box
        st.error(
            f"**Gemini Primary Model Failed → Fell back to Groq 8B**\n\n"
            f"**Error Type:** {error_type}\n\n"
            f"**Tip:** {error_tip}"
        )

        # Collapsible raw error details
        with st.expander("🔍 View Raw Error Details"):
            st.code(gemini_error, language="text")

            st.markdown("**Fallback Path:**")
            st.markdown("""
            ```
            ❌ gemini/gemini-2.0-flash-lite  (FAILED)
                        │
                        ▼
            ✅ groq/llama-3.1-8b-instant    (SUCCESS)
            ```
            """)

            st.markdown(f"**Primary Model:** `gemini/gemini-2.0-flash-lite`")
            st.markdown(f"**Fallback Model:** `{result['model_used']}`")
            st.markdown(f"**Fallback Latency:** `{result['latency_ms']}ms`")
    # ── Results Layout ──
    st.divider()

    # Routing summary cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🤖 Agent", routing["agent"].title())
    with col2:
        st.metric("📊 Complexity", routing["complexity"].title())
    with col3:
        st.metric("⚡ Model Tier", routing["tier"].title())
    with col4:
        st.metric("🔧 Total Tokens", result["total_tokens"])

    # Response
    st.subheader("📝 Response")
    st.markdown(result["response"])

    # ── Metrics Row ──
    st.divider()
    st.subheader("📊 Performance Metrics")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Routing Latency", f"{routing['routing_latency_ms']}ms")
    with m2:
        st.metric("Agent Latency", f"{result['latency_ms']}ms")
    with m3:
        st.metric("Total Latency", f"{routing['routing_latency_ms'] + result['latency_ms']:.0f}ms")
    with m4:
        st.metric("Est. Cost", f"${result['estimated_cost']:.6f}")

    # ── Cost Comparison Table ──
    st.divider()
    st.subheader("💰 Cost & Latency Comparison — Why Dynamic Routing Matters")

    comparisons = compute_comparison(result)
    df = pd.DataFrame(comparisons)
    df["savings_vs_pro"] = ""

    pro_cost = next(c["est_cost"] for c in comparisons if c["tier"] == "pro")
    pro_latency = next(c["avg_latency_ms"] for c in comparisons if c["tier"] == "pro")

    for i, row in df.iterrows():
        if row["tier"] != "pro" and pro_cost > 0:
            cost_saving = ((pro_cost - row["est_cost"]) / pro_cost) * 100
            latency_saving = ((pro_latency - row["avg_latency_ms"]) / pro_latency) * 100
            df.at[i, "savings_vs_pro"] = f"💰 {cost_saving:.0f}% cheaper, ⚡ {latency_saving:.0f}% faster"
        elif row["tier"] == "pro":
            df.at[i, "savings_vs_pro"] = "Baseline"

    # Highlight selected row
    display_df = df[["label", "model", "est_cost", "avg_latency_ms", "was_selected", "savings_vs_pro"]].copy()
    display_df.columns = ["Tier", "Model", "Est. Cost ($)", "Avg Latency (ms)", "Selected ✓", "Savings vs Pro"]
    display_df["Est. Cost ($)"] = display_df["Est. Cost ($)"].apply(lambda x: f"${x:.6f}")
    display_df["Selected ✓"] = display_df["Selected ✓"].apply(lambda x: "✅" if x else "")

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Insight box
    selected_tier = result["tier"]
    if selected_tier != "pro":
        actual_cost = result["estimated_cost"]
        saving_pct = ((pro_cost - actual_cost) / pro_cost * 100) if pro_cost > 0 else 0
        st.success(
            f"🎯 **Smart Routing saved ~{saving_pct:.0f}% cost** by using **{result['model_label']}** "
            f"instead of Pro for this {routing['complexity']} {routing['agent']} task!"
        )
    else:
        st.info("🔴 **Pro model selected** — this task required maximum capability. No downgrade possible without quality loss.")

    # ── Detailed Breakdown (collapsible) ──
    with st.expander("🔍 Full Execution Details"):
        st.json({
            "routing": routing,
            "execution": {
                "model": result["model_used"],
                "label": result["model_label"],
                "tier": result["tier"],
                "agent": result["agent"],
                "latency_ms": result["latency_ms"],
                "prompt_tokens": result["prompt_tokens"],
                "completion_tokens": result["completion_tokens"],
                "total_tokens": result["total_tokens"],
                "estimated_cost": result["estimated_cost"],
            },
        })

elif not query.strip() and st.session_state.get("_run_clicked"):
    st.warning("Please enter a query first.")

# ── Footer ──
st.divider()
st.caption("Built with LiteLLM + Groq + Gemini | Prototype for dynamic model routing demonstration")