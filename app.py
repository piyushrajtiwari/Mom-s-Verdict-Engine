"""
app.py — Streamlit UI for Moms Verdict Engine (Groq API)

Run:
    streamlit run app.py
"""

import json
import time
import streamlit as st
from main import run_pipeline

# ─── Page Config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Mom's Verdict Engine",
    page_icon="🧠",
    layout="wide",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Mono', monospace; }

.header {
  background: linear-gradient(135deg,#0f0f0f,#1a1a2e);
  border:1px solid #4ade80; border-radius:8px;
  padding:22px 28px; margin-bottom:20px;
}
.header h1 { color:#4ade80; font-size:1.8rem; margin:0; }
.header p  { color:#94a3b8; margin:4px 0 0; font-size:.82rem; }

.metric-card {
  background:#111; border:1px solid #334155;
  border-radius:6px; padding:14px; text-align:center;
}
.metric-card .lbl { color:#64748b; font-size:.72rem; text-transform:uppercase; letter-spacing:.06em; }
.metric-card .val { color:#f1f5f9; font-size:1.8rem; font-weight:600; }
.metric-card .sub { color:#94a3b8; font-size:.68rem; margin-top:2px; }

.pro  { border-left:3px solid #4ade80; padding:10px 14px; margin:5px 0; background:#0d1f0d; border-radius:4px; }
.con  { border-left:3px solid #f87171; padding:10px 14px; margin:5px 0; background:#1f0d0d; border-radius:4px; }
.tag  { display:inline-block; background:#1e293b; border:1px solid #334155; color:#94a3b8;
        border-radius:4px; padding:1px 7px; font-size:.7rem; margin:2px; }

.sum-en { background:#0f172a; border:1px solid #1e3a5f; border-radius:6px; padding:14px; color:#cbd5e1; line-height:1.7; }
.sum-ar { background:#1a0f2e; border:1px solid #3b1f5f; border-radius:6px; padding:14px;
          color:#c4b5fd; line-height:1.9; direction:rtl; text-align:right; }

.warn { background:#431407; border:1px solid #ea580c; color:#fb923c;
        border-radius:4px; padding:8px 12px; margin:4px 0; font-size:.8rem; }
.unk  { background:#1c1917; border:1px solid #57534e; color:#a8a29e;
        border-radius:4px; padding:8px 12px; margin:4px 0; font-size:.8rem; }

.stButton > button {
  background:#4ade80; color:#0f0f0f; font-family:'IBM Plex Mono',monospace;
  font-weight:600; border:none; border-radius:4px; padding:10px 28px; width:100%;
}
.stButton > button:hover { background:#86efac; }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────────────────

EXAMPLES = {
    "All Positive": "\n".join([
        "Absolutely love this product! Best purchase I've made all year.",
        "Incredible build quality, fast performance, great value.",
        "Battery lasts 3 days. Screen is gorgeous.",
    ]),
    "All Negative": "\n".join([
        "Terrible product. Broke after one week.",
        "Awful quality. Waste of money. Do not buy.",
        "Battery lasts 30 minutes. Completely useless.",
    ]),
    "Mixed Conflict": "\n".join([
        "Battery life is excellent! Lasts all day easily.",
        "Battery drains within 2 hours. Very disappointed.",
        "Great camera quality. Photos are stunning.",
        "Camera is mediocre, nothing special.",
    ]),
    "Arabic Heavy": "\n".join([
        "المنتج رائع جداً. الجودة ممتازة والسعر مناسب.",
        "البطارية تدوم لفترة طويلة جداً. أنصح بشرائه.",
        "الشاشة جميلة والألوان واضحة ومشرقة.",
    ]),
    "Noisy Spam": "\n".join([
        "GREAT PRODUCT!!!! 5 STARS!!!!!!",
        "asdfjkl; asdfjkl;",
        "Good product. Works as expected.",
        "Solid build. No issues after 3 months.",
    ]),
}

with st.sidebar:
    st.markdown("### ⚙️ Load Example")
    example = st.selectbox("Select", ["None"] + list(EXAMPLES.keys()))
    st.markdown("---")
    st.markdown("""
### 📐 Pipeline
`RAG (FAISS + multilingual embeddings)`  
`→ Pros Extractor`  
`→ Cons Extractor`  
`→ Conflict Detector`  
`→ Summary (EN + AR)`  
`→ Scoring Engine`  
`→ Pydantic Validation`

### 🔑 Model
**Groq:** llama-3.3-70b-versatile  
**Embeddings:** paraphrase-multilingual-MiniLM-L12-v2
""")

# ─── Header ──────────────────────────────────────────────────────────────────

st.markdown("""
<div class="header">
  <h1>🧠 Mom's Verdict Engine</h1>
  <p>Multilingual product review analysis · English + Arabic · Groq API + FAISS RAG</p>
</div>
""", unsafe_allow_html=True)

# ─── Input ────────────────────────────────────────────────────────────────────

default = EXAMPLES.get(example, "") if example != "None" else ""

st.markdown("#### 📝 Paste Reviews — one per line (English, Arabic, or mixed)")
text = st.text_area("reviews", value=default, height=190, label_visibility="collapsed",
                    placeholder="Paste reviews here...")

col_btn, col_info = st.columns([1, 4])
with col_btn:
    go = st.button("▶ Analyse")
with col_info:
    n = len([r for r in text.strip().split("\n") if r.strip()])
    if text.strip():
        st.caption(f"📦 {n} review{'s' if n != 1 else ''} ready")

# ─── Run ──────────────────────────────────────────────────────────────────────

if go:
    reviews = [r.strip() for r in text.strip().split("\n") if r.strip()]

    with st.spinner("🔍 Running pipeline (RAG → Extract → Conflict → Summary → Score)…"):
        t0 = time.time()
        try:
            out = run_pipeline(reviews)
        except Exception as exc:
            st.error(f"Pipeline error: {exc}")
            st.exception(exc)
            st.stop()

    elapsed = time.time() - t0

    # ── Metrics ──────────────────────────────────────────────────────────────
    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        stars = "⭐" * max(0, round(out["rating"]))
        st.markdown(f'<div class="metric-card"><div class="lbl">Rating</div>'
                    f'<div class="val">{out["rating"]}</div>'
                    f'<div class="sub">{stars} / 5.0</div></div>', unsafe_allow_html=True)
    with m2:
        pct = int(out["confidence_score"] * 100)
        col = "#4ade80" if pct >= 70 else "#fbbf24" if pct >= 40 else "#f87171"
        st.markdown(f'<div class="metric-card"><div class="lbl">Confidence</div>'
                    f'<div class="val" style="color:{col}">{pct}%</div>'
                    f'<div class="sub">pipeline certainty</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card"><div class="lbl">Pros / Cons</div>'
                    f'<div class="val">{len(out["pros"])} / {len(out["cons"])}</div>'
                    f'<div class="sub">extracted aspects</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-card"><div class="lbl">Time</div>'
                    f'<div class="val">{elapsed:.1f}s</div>'
                    f'<div class="sub">pipeline duration</div></div>', unsafe_allow_html=True)

    # ── Summaries ─────────────────────────────────────────────────────────────
    st.markdown("---")
    ce, ca = st.columns(2)
    with ce:
        st.markdown("#### 🇬🇧 English Summary")
        st.markdown(f'<div class="sum-en">{out["summary_en"]}</div>', unsafe_allow_html=True)
    with ca:
        st.markdown("#### 🇸🇦 Arabic Summary")
        st.markdown(f'<div class="sum-ar">{out["summary_ar"]}</div>', unsafe_allow_html=True)

    # ── Pros & Cons ───────────────────────────────────────────────────────────
    st.markdown("---")
    cp, cc = st.columns(2)

    with cp:
        st.markdown("#### ✅ Pros")
        if out["pros"]:
            for p in out["pros"]:
                st.markdown(
                    f'<div class="pro"><strong>{p["aspect"]}</strong> '
                    f'<span class="tag">conf {int(p["confidence"]*100)}%</span>'
                    f'<span class="tag">+{p["rating_impact"]:.2f}</span>'
                    f'<br><small style="color:#64748b">{p["evidence"]}</small></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No pros identified.")

    with cc:
        st.markdown("#### ❌ Cons")
        if out["cons"]:
            for c in out["cons"]:
                st.markdown(
                    f'<div class="con"><strong>{c["aspect"]}</strong> '
                    f'<span class="tag">conf {int(c["confidence"]*100)}%</span>'
                    f'<span class="tag">{c["rating_impact"]:.2f}</span>'
                    f'<br><small style="color:#64748b">{c["evidence"]}</small></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No cons identified.")

    # ── Disagreements & Unknowns ──────────────────────────────────────────────
    st.markdown("---")
    cd, cu = st.columns(2)
    with cd:
        st.markdown("#### ⚡ Disagreements")
        if out["disagreements"]:
            for d in out["disagreements"]:
                st.markdown(f'<div class="warn">⚡ {d}</div>', unsafe_allow_html=True)
        else:
            st.success("No significant disagreements detected.")
    with cu:
        st.markdown("#### ❓ Unknowns")
        if out["unknowns"]:
            for u in out["unknowns"]:
                st.markdown(f'<div class="unk">❓ {u}</div>', unsafe_allow_html=True)
        else:
            st.success("No unknowns flagged.")

    # ── Raw JSON ─────────────────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("🔍 Raw JSON Output"):
        st.json(out)