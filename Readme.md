# 🧠 Mom's Verdict Engine

### Multilingual Product Reviews → Structured Insights with AI

> **Track A Submission — Mumzworld AI Engineering Intern**
> Built to solve a real e-commerce problem: helping parents make faster and better buying decisions from overwhelming product reviews.

---

# 📌 Overview

Parents shopping online often face **review overload** — hundreds of comments, mixed opinions, different languages, and conflicting experiences.

**Mom’s Verdict Engine** is an AI-powered system that transforms raw customer reviews (English, Arabic, or mixed) into a clear, structured product verdict in seconds.

Instead of manually reading reviews, users instantly get:

✅ Summary
✅ Pros & Cons
✅ Reviewer Conflicts
✅ Confidence Score
✅ Final Rating
✅ English + Arabic Output

---

# 🎯 Why This Matters for Mumzworld

Mumzworld customers are busy parents who need quick, trustworthy decisions.

This solution improves the shopping experience by converting unstructured reviews into instant insights.

### Business Impact

* 📈 Faster purchase decisions
* 🛒 Higher product page conversion rates
* 🤝 Increased customer trust
* 🌍 Better Arabic + English accessibility
* 📉 Reduced bounce caused by decision fatigue
* ⭐ Stronger review usefulness on product pages

---

# 🚀 Features

## 🔍 Smart Review Understanding

* Handles noisy or short reviews
* Supports multilingual text
* Detects spam / irrelevant inputs
* Finds hidden sentiment patterns
* Identifies recurring product issues

---

## 📊 Structured JSON Output

Returns:

* `summary_en`
* `summary_ar`
* `pros[]`
* `cons[]`
* `rating`
* `confidence_score`
* `disagreements[]`
* `unknowns[]`

---

## ⚙️ LangGraph AI Workflow

7-step agentic pipeline:

1. RAG Retrieval
2. Pros Extraction
3. Cons Extraction
4. Conflict Detection
5. Summary Generation
6. Product Scoring
7. Final Validation

---

# 🌍 Multilingual Support

✅ English
✅ Arabic
✅ Mixed Reviews

---

# 🎥 Demo Walkthrough

### GitHub Repository

https://github.com/piyushrajtiwari/Mom-s-Verdict-Engine

### Demo Video

https://drive.google.com/file/d/1gqfFmL44KwiId9jSCZzGFpiZBQdaBmp7/view?usp=sharing

---

# 📂 Project Structure

```bash
moms_verdict_engine/
├── .env.example
├── config.py
├── state.py
├── prompts.py
├── rag.py
├── nodes.py
├── main.py
├── evals.py
├── app.py
├── requirements.txt
└── README.md
```

---

# ⚡ Quick Setup

## 1️⃣ Clone Repository

```bash
git clone https://github.com/piyushrajtiwari/Mom-s-Verdict-Engine.git
cd Mom-s-Verdict-Engine
```

## 2️⃣ Create Virtual Environment

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Mac / Linux

```bash
source .venv/bin/activate
```

## 3️⃣ Install Requirements

```bash
pip install -r requirements.txt
```

## 4️⃣ Configure Environment

Create `.env`

```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Get free API key:
https://console.groq.com

---

# ▶️ Run the App

```bash
streamlit run app.py
```

# 💻 Run in Terminal

```bash
python main.py
```

# 🧪 Run Evaluations

```bash
python evals.py
```

Single test:

```bash
python evals.py --case empty_input
```

By tag:

```bash
python evals.py --tag arabic
```

---

# 🧠 System Architecture

```text
Streamlit UI
   ↓
run_pipeline()
   ↓
LangGraph Workflow
   ↓
[1] rag_node
[2] pros_node
[3] cons_node
[4] conflict_node
[5] summary_node
[6] scoring_node
[7] validation_node
   ↓
Final JSON Verdict
```

---

# 🔥 Example Output

```json
{
  "summary_en": "Battery is excellent but build quality is weak.",
  "summary_ar": "البطارية ممتازة لكن جودة التصنيع ضعيفة.",
  "pros": [
    {
      "aspect": "Battery",
      "confidence": 0.94,
      "evidence": "Lasts 3 days",
      "rating_impact": 0.8
    }
  ],
  "cons": [
    {
      "aspect": "Build",
      "confidence": 0.87,
      "evidence": "Broken in one week",
      "rating_impact": -0.9
    }
  ],
  "rating": 3.6,
  "confidence_score": 0.74,
  "disagreements": [
    "Some users say charging is fast, others say slow."
  ],
  "unknowns": [
    "Camera quality mentioned only once."
  ]
}
```

---

# 🧪 Validation / Proof It Works

Tested across multiple scenarios:

| #  | Case                 | Goal                    |
| -- | -------------------- | ----------------------- |
| 1  | all_positive         | Detect strong positives |
| 2  | all_negative         | Detect negatives        |
| 3  | mixed_conflicting    | Handle conflicts        |
| 4  | arabic_heavy         | Arabic understanding    |
| 5  | noisy_spam           | Ignore spam             |
| 6  | empty_input          | Graceful fallback       |
| 7  | direct_contradiction | Detect disagreement     |
| 8  | irrelevant_text      | Robust filtering        |
| 9  | short_reviews        | Sparse data handling    |
| 10 | long_reviews         | Long context handling   |
| 11 | single_review        | Limited evidence        |
| 12 | multilingual_mixed   | Mixed language support  |

### Expected Outcomes

✅ Stable structured JSON
✅ Useful summaries
✅ Accurate pros/cons extraction
✅ Conflict detection
✅ Graceful handling of weak inputs

---

# ⚖️ Tradeoffs & Decisions

### Why Groq API?

Used Groq because it offers fast inference with free-tier access.

### Why FAISS?

Simple, lightweight local vector database with no external dependency.

### Why LangGraph?

Better for multi-step workflows than a single prompt call.

### Known Limitations

* LLM outputs may vary slightly between runs
* Very limited review data reduces confidence
* Sarcasm / vague comments can be harder to interpret

### Design Priority

Focused on:

* Explainability
* Structured outputs
* Real business usefulness
* Fast prototype delivery

---

# 🛠️ Tools & Tech Stack

| Category   | Tools                 |
| ---------- | --------------------- |
| Language   | Python                |
| LLM        | Groq API              |
| Workflow   | LangGraph             |
| Retrieval  | FAISS                 |
| Embeddings | sentence-transformers |
| UI         | Streamlit             |
| Config     | dotenv                |

---

# 🤖 AI Tools & Workflow Transparency

Used AI tools responsibly during development:

* ChatGPT → brainstorming, debugging
* Groq API → model inference
* Sentence Transformers → embeddings
* LangGraph → orchestration
* Streamlit → frontend prototype

All final implementation, integration, testing, and customization were completed by me.


# 🔮 Future Improvements

* Hindi support 🇮🇳
* Dashboard analytics
* Sentiment charts
* Human feedback loop
* Product comparison mode
* Review trend tracking

---

# 🤝 Contributing

1. Fork repo
2. Create branch
3. Commit changes
4. Open Pull Request

---

# 📜 License

MIT License

---

# ⭐ Final Note

Built with ❤️ using Python + AI
For the Mumzworld AI Engineering Intern Challenge
