# 🧠 Mom's Verdict Engine

> Multilingual Product Reviews → Structured Insights with AI

---

## 📌 Overview

**Mom’s Verdict Engine** is an AI-powered system that transforms raw customer reviews (English, Arabic, or mixed) into a structured product verdict.

Instead of reading hundreds of reviews manually, users instantly get:

* ✅ Summary
* ✅ Pros & Cons
* ✅ Conflicts between reviewers
* ✅ Confidence Score
* ✅ Final Rating
* ✅ Multilingual Output

---

## 🚀 Features

### 🔍 Smart Review Understanding

* Handles noisy reviews
* Supports multilingual text
* Detects spam / irrelevant inputs
* Finds hidden sentiment patterns

### 📊 Structured JSON Output

Returns:

* `summary_en`
* `summary_ar`
* `pros[]`
* `cons[]`
* `rating`
* `confidence_score`
* `disagreements[]`
* `unknowns[]`

### ⚙️ LangGraph Pipeline

7-step workflow:

1. RAG Retrieval
2. Pros Extraction
3. Cons Extraction
4. Conflict Detection
5. Summary Generation
6. Product Scoring
7. Final Validation

### 🌍 Multilingual Support

* English
* Arabic
* Mixed Reviews

---

## 📂 Project Structure

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
└── requirements.txt
```

---

## ⚡ Quick Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/yourusername/moms_verdict_engine.git
cd moms_verdict_engine
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv .venv
```

**Windows**

```bash
.venv\Scripts\activate
```

**Mac/Linux**

```bash
source .venv/bin/activate
```

### 3️⃣ Install Requirements

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure `.env`

```env
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Get free key: https://console.groq.com

---

## ▶️ Run App

```bash
streamlit run app.py
```

---

## 💻 Run in Terminal

```bash
python main.py
```

---

## 🧪 Run Tests

```bash
python evals.py
```

Single case:

```bash
python evals.py --case empty_input
```

By tag:

```bash
python evals.py --tag arabic
```

---

## 🧠 Architecture

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

## 🔥 Output Example

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

## 🧪 Evaluation Cases

| #  | Case                 | Tags          |
| -- | -------------------- | ------------- |
| 1  | all_positive         | positive      |
| 2  | all_negative         | negative      |
| 3  | mixed_conflicting    | conflict      |
| 4  | arabic_heavy         | arabic        |
| 5  | noisy_spam           | noisy         |
| 6  | empty_input          | edge          |
| 7  | direct_contradiction | contradiction |
| 8  | irrelevant_text      | edge          |
| 9  | short_reviews        | sparse        |
| 10 | long_reviews         | verbose       |
| 11 | single_review        | sparse        |
| 12 | multilingual_mixed   | mixed         |

---

## ⚡ Supported Groq Models

| Model                   | Best For        |
| ----------------------- | --------------- |
| llama-3.3-70b-versatile | Best Quality    |
| llama-3.1-8b-instant    | Fast            |
| mixtral-8x7b-32768      | Structured JSON |

---

## 📈 Why This Project Matters

* ✅ Real-world use case
* ✅ Modern GenAI stack
* ✅ Vector Search + LLM
* ✅ Agentic workflow
* ✅ Resume-worthy project

Perfect for:

* Data Science Portfolio
* GenAI Internship
* AI Engineer Resume
* Product Demo

---

## 🔮 Future Improvements

* Hindi support 🇮🇳
* Dashboard analytics
* Sentiment charts
* PDF reports
* Human feedback loop

---

## 🤝 Contributing

1. Fork repo
2. Create branch
3. Commit changes
4. Open Pull Request

---

## 📜 License

MIT License

---

## ⭐ Star This Repo

Made with ❤️ using Python + AI
