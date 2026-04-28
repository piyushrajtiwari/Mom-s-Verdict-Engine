"""
evals.py — Evaluation Suite for Moms Verdict Engine
12 test cases covering every failure mode.

Usage:
    python evals.py                     # run all
    python evals.py --case empty_input  # specific case
    python evals.py --tag arabic        # by tag
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from main import run_pipeline


# ─── Assertion Library ────────────────────────────────────────────────────────

def assert_json_valid(o: dict) -> Optional[str]:
    required = ["summary_en","summary_ar","pros","cons",
                "rating","confidence_score","disagreements","unknowns"]
    missing = [k for k in required if k not in o]
    return f"Missing keys: {missing}" if missing else None

def assert_has_pros(o: dict) -> Optional[str]:
    return None if o.get("pros") else "Expected at least one pro"

def assert_has_cons(o: dict) -> Optional[str]:
    return None if o.get("cons") else "Expected at least one con"

def assert_has_disagreements(o: dict) -> Optional[str]:
    return None if o.get("disagreements") else "Expected at least one disagreement"

def assert_rating_range(o: dict, lo: float, hi: float) -> Optional[str]:
    r = o.get("rating", -1)
    return None if lo <= r <= hi else f"rating={r} not in [{lo}, {hi}]"

def assert_low_confidence(o: dict, threshold: float = 0.5) -> Optional[str]:
    c = o.get("confidence_score", 1.0)
    return None if c < threshold else f"confidence={c} >= {threshold}"

def assert_arabic_summary(o: dict) -> Optional[str]:
    ar = o.get("summary_ar", "")
    has_arabic = any('\u0600' <= c <= '\u06FF' for c in ar)
    return None if has_arabic else "summary_ar has no Arabic characters"

def assert_idk_behavior(o: dict) -> Optional[str]:
    en = o.get("summary_en", "").lower()
    ar = o.get("summary_ar", "")
    signal = (
        "don't know" in en or "لا أعلم" in ar
        or "insufficient" in en or "no reviews" in en
        or (o.get("rating", 1.0) == 0.0
            and not o.get("pros") and not o.get("cons"))
    )
    return None if signal else "Expected 'I don't know' behavior"


# ─── Test Case Definition ─────────────────────────────────────────────────────

@dataclass
class TestCase:
    name:        str
    description: str
    reviews:     list[str]
    assertions:  list[Callable[[dict], Optional[str]]]
    tags:        list[str] = field(default_factory=list)


# ─── 12 Test Cases ────────────────────────────────────────────────────────────

TEST_CASES: list[TestCase] = [

    TestCase(
        name="all_positive",
        description="All reviews clearly positive → high rating, pros present.",
        reviews=[
            "Absolutely love this product! Best purchase I've made all year.",
            "Incredible build quality, fast performance, great value for money.",
            "Battery lasts 3 days on a single charge. Screen is gorgeous.",
            "Customer support was responsive and resolved my issue in minutes.",
            "Works perfectly out of the box. Highly recommended.",
        ],
        assertions=[
            assert_json_valid,
            assert_has_pros,
            lambda o: assert_rating_range(o, 3.5, 5.0),
        ],
        tags=["positive", "en"],
    ),

    TestCase(
        name="all_negative",
        description="All reviews clearly negative → low rating, cons present.",
        reviews=[
            "Terrible product. Broke after one week of light use.",
            "Awful quality. Complete waste of money. Do not buy.",
            "Battery drains in 30 minutes. Completely useless.",
            "Customer service ignored my complaint entirely.",
            "Worst purchase of my life. Returned immediately.",
        ],
        assertions=[
            assert_json_valid,
            assert_has_cons,
            lambda o: assert_rating_range(o, 0.0, 2.5),
        ],
        tags=["negative", "en"],
    ),

    TestCase(
        name="mixed_conflicting",
        description="Reviewers disagree on key aspects → disagreements detected.",
        reviews=[
            "Battery life is excellent! Lasts all day without any issues.",
            "Battery drains within 2 hours. Very disappointed.",
            "Great camera quality. Photos are sharp and stunning.",
            "Camera is mediocre at best. Nothing special, overhyped.",
            "Price is fair for what you get.",
            "Way overpriced. Not worth a fraction of the cost.",
        ],
        assertions=[
            assert_json_valid,
            assert_has_pros,
            assert_has_cons,
            assert_has_disagreements,
        ],
        tags=["mixed", "conflict", "en"],
    ),

    TestCase(
        name="arabic_heavy",
        description="Mostly Arabic reviews → Arabic summary with Arabic characters.",
        reviews=[
            "المنتج رائع جداً. الجودة ممتازة والسعر مناسب جداً.",
            "البطارية تدوم لفترة طويلة جداً. أنصح بشرائه بشدة.",
            "الشاشة جميلة جداً والألوان واضحة ومشرقة.",
            "خدمة العملاء ممتازة. ردوا علي بسرعة وحلوا مشكلتي.",
            "سهل الاستخدام جداً. حتى كبار السن يمكنهم استخدامه.",
        ],
        assertions=[
            assert_json_valid,
            assert_arabic_summary,
            lambda o: assert_rating_range(o, 3.0, 5.0),
        ],
        tags=["arabic", "positive"],
    ),

    TestCase(
        name="noisy_spam",
        description="Spam + garbage + real reviews → signal extracted from noise.",
        reviews=[
            "GREAT PRODUCT!!!! 5 STARS!!!!!! BUY NOW!!!!",
            "asdfjkl; asdfjkl; asdfjkl;",
            "👍👍👍👍👍 best ever 👍👍👍👍👍",
            "Good product. Solid build quality, works as expected.",
            "lorem ipsum dolor sit amet consectetur adipiscing elit",
            "No issues after 3 months of daily use. Reliable.",
        ],
        assertions=[
            assert_json_valid,
            lambda o: assert_rating_range(o, 2.0, 5.0),
        ],
        tags=["noisy", "spam"],
    ),

    TestCase(
        name="empty_input",
        description="No reviews → 'I don't know' behavior, near-zero confidence.",
        reviews=[],
        assertions=[
            assert_json_valid,
            assert_idk_behavior,
            lambda o: assert_low_confidence(o, threshold=0.3),
        ],
        tags=["edge_case", "empty"],
    ),

    TestCase(
        name="direct_contradiction",
        description="Same aspect praised and slammed → disagreements flagged.",
        reviews=[
            "The build quality is phenomenal. Solid metal, premium feel.",
            "Build quality is shockingly bad. Cheap plastic that breaks easily.",
            "Feels premium and very sturdy in the hand.",
            "Fell apart after a week. Cheapest quality I've ever seen.",
        ],
        assertions=[
            assert_json_valid,
            assert_has_disagreements,
        ],
        tags=["contradiction", "conflict"],
    ),

    TestCase(
        name="irrelevant_text",
        description="Off-topic text only → 'I don't know', no fabricated insights.",
        reviews=[
            "The weather today is very nice. I love sunny days.",
            "My cat's name is Whiskers and she loves tuna.",
            "Did you know the capital of France is Paris?",
            "I enjoy long walks on the beach at sunset.",
        ],
        assertions=[
            assert_json_valid,
            assert_idk_behavior,
        ],
        tags=["edge_case", "irrelevant"],
    ),

    TestCase(
        name="short_reviews",
        description="Single words / fragments → low confidence due to weak evidence.",
        reviews=[
            "Good.", "Bad.", "Okay.", "Love it.",
            "Hate it.", "Fine.", "Meh.",
        ],
        assertions=[
            assert_json_valid,
            lambda o: assert_low_confidence(o, threshold=0.7),
        ],
        tags=["edge_case", "short"],
    ),

    TestCase(
        name="long_reviews",
        description="Extremely verbose reviews → pipeline handles large input correctly.",
        reviews=[
            (
                "I have been using this product for approximately six months now and I must say "
                "that my experience has been nothing short of exceptional. The build quality is "
                "outstanding — every component feels precision-engineered. The battery performance "
                "is particularly impressive; I routinely get three full days before needing to "
                "charge. The display resolution and color accuracy are class-leading. Software "
                "updates have been consistent. Customer support resolved my one minor issue within "
                "24 hours. Highly recommended without reservation."
            ),
            (
                "After extensive testing across multiple use scenarios I can confidently say this "
                "product falls short in several key areas. Thermal management is insufficient: "
                "the device becomes uncomfortably warm under sustained load. The software ecosystem "
                "is limited compared to competitors. Charging speed lags behind similarly priced "
                "alternatives. Build quality is adequate but not exceptional. On the positive side, "
                "the display is genuinely impressive and audio output is surprisingly powerful. "
                "Overall a mixed bag."
            ),
        ],
        assertions=[
            assert_json_valid,
            assert_has_pros,
            assert_has_cons,
        ],
        tags=["long", "verbose"],
    ),

    TestCase(
        name="single_review",
        description="Only one review → confidence capped (sparse data).",
        reviews=["Decent product. Works fine."],
        assertions=[
            assert_json_valid,
            lambda o: assert_low_confidence(o, threshold=0.5),
        ],
        tags=["edge_case", "sparse"],
    ),

    TestCase(
        name="multilingual_mixed",
        description="English + Arabic reviews mixed → Arabic summary, pros extracted.",
        reviews=[
            "Amazing product, love the design and performance.",
            "المنتج جيد لكن السعر مرتفع قليلاً.",
            "Battery could be better but overall very satisfied.",
            "الجودة ممتازة والتصميم أنيق جداً.",
            "Some minor software bugs, otherwise excellent.",
            "أحتاج إلى تحسين في خدمة العملاء.",
        ],
        assertions=[
            assert_json_valid,
            assert_arabic_summary,
            assert_has_pros,
        ],
        tags=["multilingual", "en", "arabic"],
    ),
]


# ─── Eval Runner ──────────────────────────────────────────────────────────────

@dataclass
class EvalResult:
    name:       str
    passed:     bool
    failures:   list[str]
    output:     dict
    duration_s: float
    tags:       list[str]


def run_eval(tc: TestCase) -> EvalResult:
    print(f"\n{'─'*60}")
    print(f"  TEST  : {tc.name}")
    print(f"  DESC  : {tc.description}")
    print(f"  TAGS  : {', '.join(tc.tags)}")
    print(f"  INPUT : {len(tc.reviews)} review(s)")

    t0 = time.time()
    try:
        output = run_pipeline(tc.reviews)
    except Exception as exc:
        dur = round(time.time() - t0, 2)
        print(f"  ❌  EXCEPTION: {exc}")
        return EvalResult(tc.name, False, [f"Exception: {exc}"], {}, dur, tc.tags)

    dur = round(time.time() - t0, 2)
    failures = [msg for a in tc.assertions if (msg := a(output))]
    passed = len(failures) == 0

    print(f"  rating          : {output.get('rating')}")
    print(f"  confidence_score: {output.get('confidence_score')}")
    print(f"  pros            : {len(output.get('pros', []))}")
    print(f"  cons            : {len(output.get('cons', []))}")
    print(f"  disagreements   : {len(output.get('disagreements', []))}")
    print(f"  unknowns        : {len(output.get('unknowns', []))}")
    print(f"  summary_en      : {output.get('summary_en','')[:80]}...")
    print(f"  duration        : {dur}s")

    if passed:
        print("  ✅  PASSED")
    else:
        for f in failures:
            print(f"  ❌  FAILED: {f}")

    return EvalResult(tc.name, passed, failures, output, dur, tc.tags)


def run_all(cases: list[TestCase]) -> list[EvalResult]:
    results = [run_eval(tc) for tc in cases]
    passed  = sum(1 for r in results if r.passed)
    total   = len(results)
    avg_dur = round(sum(r.duration_s for r in results) / total, 2) if total else 0

    print(f"\n{'='*60}")
    print(f"  EVAL SUMMARY")
    print(f"  Passed  : {passed}/{total}")
    print(f"  Failed  : {total - passed}/{total}")
    print(f"  Avg dur : {avg_dur}s")
    print(f"{'='*60}")
    for r in results:
        icon = "✅" if r.passed else "❌"
        print(f"  {icon}  {r.name:<32} ({r.duration_s:.1f}s)")

    return results


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Moms Verdict Engine evals")
    parser.add_argument("--case", help="Run one test case by name")
    parser.add_argument("--tag",  help="Run test cases matching a tag")
    args = parser.parse_args()

    cases = TEST_CASES
    if args.case:
        cases = [tc for tc in TEST_CASES if tc.name == args.case]
        if not cases:
            print(f"No test case named '{args.case}'")
            sys.exit(1)
    elif args.tag:
        cases = [tc for tc in TEST_CASES if args.tag in tc.tags]
        if not cases:
            print(f"No test cases with tag '{args.tag}'")
            sys.exit(1)

    results = run_all(cases)
    sys.exit(0 if all(r.passed for r in results) else 1)