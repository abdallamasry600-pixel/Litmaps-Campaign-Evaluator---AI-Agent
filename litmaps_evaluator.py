import os
import json
import streamlit as st
import google.generativeai as genai

# Read API Key from Environment Variable
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)


def evaluate_litmaps_campaign(channel, content_text, open_rate, ctr):
    """
    Calls Gemini and asks for a STRUCTURED JSON response so we can
    render the score, strengths/weaknesses, and improved copy variants
    as clean UI elements instead of raw markdown text.
    """
    model = genai.GenerativeModel("gemini-flash-latest")

    prompt = f"""
    You are a Senior Digital Marketing Strategist for B2B SaaS and Academic EdTech platforms.
    Evaluate the following digital campaign copy promoting 'Litmaps' (a visual literature research mapping tool):

    - Channel: {channel}
    - Campaign Text: \"\"\"{content_text}\"\"\"
    - Key Metrics: Expected Open Rate: {open_rate}%, Expected CTR: {ctr}%

    Return ONLY valid JSON (no markdown fences, no preamble, no extra text) matching
    exactly this schema:

    {{
      "performance_score": <integer 0-100>,
      "benchmark_evaluation": "<2-3 sentence evaluation vs EdTech/SaaS industry benchmarks>",
      "strengths": ["<point 1>", "<point 2>", "..."],
      "weaknesses": ["<point 1>", "<point 2>", "..."],
      "improved_variants": [
        {{
          "label": "<short name for this variant's angle, e.g. 'Curiosity-driven'>",
          "subject_line": "<a rewritten subject line / headline for this channel>",
          "cta": "<a rewritten call-to-action>",
          "rationale": "<1 sentence on why this should perform better>"
        }},
        {{
          "label": "<short name for this variant's angle>",
          "subject_line": "<...>",
          "cta": "<...>",
          "rationale": "<...>"
        }},
        {{
          "label": "<short name for this variant's angle>",
          "subject_line": "<...>",
          "cta": "<...>",
          "rationale": "<...>"
        }}
      ]
    }}

    Provide exactly 3 improved_variants, each with a genuinely different angle
    (e.g. curiosity/pain-point/social-proof), tailored to researchers/academics
    and appropriate for the {channel} channel.
    """

    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    # Defensive cleanup in case the model wraps the JSON in ```json fences anyway
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:].strip()

    return json.loads(raw_text)


# Streamlit App UI
st.set_page_config(page_title="Litmaps AI Marketing Evaluator", page_icon="🗺️", layout="wide")

st.title("🗺️ Litmaps Campaign Evaluator - AI Agent")
st.caption("Novartis Competition Submission | Powered by Gemini API")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📥 Input Campaign Details")
    channel = st.selectbox("Marketing Channel:", ["Email", "WhatsApp", "LinkedIn / Social Media"])
    content_text = st.text_area(
        "Copy Text:",
        value="Struggling with literature reviews? Discover connected papers visually with Litmaps. Try it free today!",
        height=150
    )
    open_rate = st.slider("Open Rate (%):", 0.0, 100.0, 28.0)
    ctr = st.slider("Click-Through Rate - CTR (%):", 0.0, 50.0, 4.5)

    if st.button("🔍 Evaluate Campaign", type="primary"):
        if not api_key:
            st.error("API Key not found! Please set GEMINI_API_KEY in your terminal.")
        else:
            with st.spinner("Analyzing Litmaps campaign copy..."):
                try:
                    result = evaluate_litmaps_campaign(channel, content_text, open_rate, ctr)
                    st.session_state['eval_result'] = result
                except json.JSONDecodeError:
                    st.error("The model returned an unexpected format. Please try again.")
                except Exception as e:
                    st.error(f"Error generating analysis: {e}")

with col2:
    st.subheader("📊 AI Performance Report")

    if 'eval_result' in st.session_state:
        result = st.session_state['eval_result']

        # --- Score ---
        score = result.get("performance_score", 0)
        st.metric("Performance Score", f"{score} / 100")
        st.progress(min(max(score, 0), 100) / 100)

        # --- Benchmark evaluation ---
        st.markdown("#### 📈 Benchmark Evaluation")
        st.info(result.get("benchmark_evaluation", ""))

        # --- Strengths / Weaknesses ---
        s_col, w_col = st.columns(2)
        with s_col:
            st.markdown("#### ✅ Strengths")
            for point in result.get("strengths", []):
                st.markdown(f"- {point}")
        with w_col:
            st.markdown("#### ⚠️ Weaknesses")
            for point in result.get("weaknesses", []):
                st.markdown(f"- {point}")

        # --- Improved variants ---
        st.markdown("#### ✨ Suggested Improved Copy Variants")
        variants = result.get("improved_variants", [])

        for i, variant in enumerate(variants, start=1):
            with st.container(border=True):
                st.markdown(f"**Variant {i}: {variant.get('label', '')}**")
                st.markdown(f"**Subject Line / Headline:**\n> {variant.get('subject_line', '')}")
                st.markdown(f"**CTA:**\n> {variant.get('cta', '')}")
                st.caption(f"💡 {variant.get('rationale', '')}")
    else:
        st.caption("Run an evaluation to see the report here.")
