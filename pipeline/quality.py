#!/usr/bin/env python3
import re

BANNED = ("ignore previous instructions", "system prompt", "password", "api key")

def score(record):
    score = 1.0
    msgs = record.get("messages", [])
    if len(msgs) < 2: return 0.0, ["too_few_messages"]
    text = " ".join(str(x.get("content", "")) for x in msgs).strip()
    reasons=[]
    if len(text) < 80: score -= .20; reasons.append("too_short")
    if len(text) > 100000: score -= .15; reasons.append("too_long")
    if any(x in text.lower() for x in BANNED): score -= .30; reasons.append("prompt_injection_like")
    if record.get("license_status") in ("unknown", "source-specific-review-required"): score -= .05; reasons.append("license_review")
    if record.get("domain") == "coding" and "test" not in text.lower(): score -= .05; reasons.append("coding_test_missing")
    if record.get("domain") == "trading" and re.search(r"\b(buy|sell|guaranteed|profit)\b", text.lower()): score -= .15; reasons.append("trading_claim_review")
    return max(0.0, score), reasons


def accept(record, minimum=0.80):
    s,reasons=score(record)
    return s >= minimum, s, reasons
