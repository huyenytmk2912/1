#!/usr/bin/env python3
import re

BANNED=("ignore previous instructions","system prompt","password","api key")


def score(record):
    s=1.0; msgs=record.get('messages',[]); reasons=[]
    if len(msgs)<2:return 0.0,['too_few_messages']
    text=' '.join(str(x.get('content','')) for x in msgs).strip(); low=text.lower()
    if len(text)<80:s-=.2;reasons.append('too_short')
    if len(text)>100000:s-=.15;reasons.append('too_long')
    if any(x in low for x in BANNED):s-=.3;reasons.append('prompt_injection_like')
    if record.get('license_status') in ('unknown','source-specific-review-required','needs_source_review','user_supplied_review_required'):
        reasons.append('license_review')
    if record.get('domain')=='coding' and not any(x in low for x in ('test','expected behavior','pytest','assert')):
        s-=.1;reasons.append('coding_test_missing')
    if record.get('domain')=='trading' and re.search(r'\b(buy|sell|guaranteed|profit)\b',low):
        s-=.15;reasons.append('trading_claim_review')
    return max(0.0,s),reasons


def accept(record,minimum=.80):
    s,reasons=score(record)
    if 'license_review' in reasons:return False,s,reasons
    return s>=minimum,s,reasons
