"""Offline check of ingestion/extract_ask_feedback.py: scrubbing, event filtering and day merging."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingestion"))
from extract_ask_feedback import questions, scrub  # noqa: E402

assert scrub("mail me at a.b@example.com or 555-123-4567 or https://x.io/p") == "mail me at [email] or [number] or [link]"
assert scrub("  padel   in\nReno ") == "padel in Reno"
assert len(scrub("x" * 500)) == 200

rows = [
    {"day": "2026-11-01", "path": "event/ask-feedback/padel-in-reno", "title": "Padel in Reno?", "is_event": "True", "count": "2"},
    {"day": "2026-11-01", "path": "event/ask-feedback/padel-in-reno", "title": "Padel in Reno?", "is_event": "True", "count": "1"},
    {"day": "2026-11-02", "path": "event/ask-feedback/call-me", "title": "call me 415 555 0100", "is_event": "True", "count": "1"},
    {"day": "2026-11-02", "path": "event/ask-feedback/ab", "title": "ab", "is_event": "True", "count": "1"},          # too short
    {"day": "2026-11-02", "path": "event/ask-kind/refuse", "title": "refuse", "is_event": "True", "count": "9"},     # other event
    {"day": "2026-11-02", "path": "event/ask-feedback/x", "title": "not an event", "is_event": "False", "count": "9"},
]
out = questions(rows)
assert out == {("2026-11-01", "Padel in Reno?"): 3, ("2026-11-02", "call me [number]"): 1}, out
print("ask feedback extract ok")
