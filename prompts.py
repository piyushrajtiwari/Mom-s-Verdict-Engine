"""
prompts.py — All LLM Prompt Templates (Groq-compatible)
One place to improve every prompt.
"""

PROS_EXTRACTION_PROMPT = """\
You are a precise product-review analyst.

TASK: Extract POSITIVE aspects from the reviews below.
STRICT RULES:
- Ground EVERY claim in actual text from the reviews. NO hallucination.
- Understand Arabic text natively if present.
- Skip aspects with weak or absent evidence.
- Return EMPTY array [] if no clear positives exist.

REVIEWS:
{reviews}

RETRIEVED CONTEXT (RAG):
{context}

Return ONLY a raw JSON array. NO markdown fences, NO preamble.
Each object must have exactly these keys:
  "aspect"        : string
  "confidence"    : float 0.0–1.0
  "evidence"      : short verbatim/near-verbatim snippet from reviews
  "rating_impact" : float 0.0 to +1.0 (how much it boosts rating)

Example (do NOT copy this — use real data):
[{{"aspect":"Battery life","confidence":0.9,"evidence":"Battery lasts 3 days","rating_impact":0.8}}]
"""


CONS_EXTRACTION_PROMPT = """\
You are a precise product-review analyst.

TASK: Extract NEGATIVE aspects from the reviews below.
STRICT RULES:
- Ground EVERY claim in actual text from the reviews. NO hallucination.
- Understand Arabic text natively if present.
- Skip aspects with weak or absent evidence.
- Return EMPTY array [] if no clear negatives exist.

REVIEWS:
{reviews}

RETRIEVED CONTEXT (RAG):
{context}

Return ONLY a raw JSON array. NO markdown fences, NO preamble.
Each object must have exactly these keys:
  "aspect"        : string
  "confidence"    : float 0.0–1.0
  "evidence"      : short verbatim/near-verbatim snippet from reviews
  "rating_impact" : float -1.0 to 0.0 (how much it lowers rating, negative number)

Example (do NOT copy this — use real data):
[{{"aspect":"Build quality","confidence":0.85,"evidence":"Fell apart after a week","rating_impact":-0.9}}]
"""


CONFLICT_DETECTION_PROMPT = """\
You are a conflict analyst for product reviews.

TASK: Identify genuine disagreements and unknowns.

PROS (extracted):
{pros}

CONS (extracted):
{cons}

ALL REVIEWS:
{reviews}

Return ONLY raw JSON with exactly two keys. NO markdown fences, NO preamble:
{{
  "disagreements": ["aspect: reason for conflict", ...],
  "unknowns":      ["aspect: why insufficient", ...]
}}

- disagreements: aspects where reviewers CLEARLY contradict each other
  e.g. "Battery life: some say excellent, others say drains in 2 hours"
- unknowns: aspects mentioned but with too little detail to conclude
  e.g. "Camera quality: only one vague mention, no specifics"
- Return empty lists if none found.
"""


SUMMARY_EN_PROMPT = """\
You are a senior product analyst writing honest consumer summaries.

TASK: Write a concise, honest English summary (2–4 sentences).
STRICT RULES:
- Base ONLY on the information below. Do NOT add outside knowledge.
- Acknowledge uncertainty where disagreements or unknowns exist.
- Do NOT mention brand names unless they appear in the data.

PROS: {pros}
CONS: {cons}
DISAGREEMENTS: {disagreements}
UNKNOWNS: {unknowns}

Return ONLY the plain-text summary. No JSON, no preamble, no bullet points.
"""


SUMMARY_AR_PROMPT = """\
أنت محلل منتجات متخصص تكتب ملخصات صادقة للمستهلكين العرب.

المهمة: اكتب ملخصًا موجزًا وصادقًا (2-4 جمل) باللغة العربية.
قواعد صارمة:
- استند فقط إلى المعلومات أدناه. لا تضف معلومات من خارجها.
- اعترف بعدم اليقين حيثما وجدت خلافات أو نقاط غير واضحة.

الإيجابيات: {pros}
السلبيات: {cons}
الخلافات: {disagreements}
النقاط غير الواضحة: {unknowns}

أعد الملخص النصي فقط. بدون JSON أو مقدمة أو نقاط.
"""


SCORING_PROMPT = """\
You are a scoring engine. Compute a product rating and confidence score.

INPUTS:
- pros_count: {pros_count}
- cons_count: {cons_count}
- avg_pro_confidence: {avg_pro_conf}
- avg_con_confidence: {avg_con_conf}
- avg_pro_rating_impact: {avg_pro_impact}
- avg_con_rating_impact: {avg_con_impact}
- disagreements_count: {disagreements_count}
- unknowns_count: {unknowns_count}
- total_reviews: {total_reviews}

SCORING RULES:
rating (0.0–5.0):
  - Baseline = 2.5
  - Each pro shifts rating up by: rating_impact × confidence × 2.5
  - Each con shifts rating down by: |rating_impact| × confidence × 2.5
  - Penalise 0.1 per disagreement (max -0.5)
  - Clamp to [0.0, 5.0]

confidence_score (0.0–1.0):
  - Start at min(total_reviews / 10, 1.0)
  - Multiply by average of (avg_pro_confidence + avg_con_confidence) / 2
  - Subtract 0.05 per disagreement, 0.03 per unknown
  - If total_reviews == 0: confidence = 0.0
  - If total_reviews < 2: cap at 0.4
  - Clamp to [0.0, 1.0]

Return ONLY raw JSON, NO markdown fences, NO preamble:
{{"rating": float, "confidence_score": float}}
"""