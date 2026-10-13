"""Fail when a hand-edited seed row lacks the evidence ADR 0008 requires. Run in CI before dbt."""
import csv, re, sys
from pathlib import Path

SEEDS = Path(__file__).resolve().parents[1] / "transform" / "seeds"
ISO = re.compile(r"\d{4}-\d{2}-\d{2}")
RULES = {  # file: (date column, columns that must be non-empty, columns that must be https links when set)
    "manual_venues.csv": ("confirmed_on", ["evidence", "confirmation"], []),
    "venue_actions.csv": ("verified_on", ["evidence", "url"], ["url"]),
    "venue_confirmations.csv": ("confirmed_on", ["evidence", "confirmed_by", "method"], []),
    "watch_events.csv": ("verified_on", ["source_note"], ["info_url", "tickets_url"]),
}
# Older rows that predate this check and have no date. Date them (or lower them to reported) and delete the entry.
GRANDFATHERED = set()
errors = []
for name, (datecol, required, https) in RULES.items():
    with (SEEDS / name).open(newline="", encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f), start=2):
            where = f"{name}:{i}"
            if name == "manual_venues.csv" and r.get("venue_key") in GRANDFATHERED and not (r.get("confirmed_on") or "").strip():
                continue
            reported = name == "manual_venues.csv" and (r.get("confirmation") or "").strip() == "reported"   # the floor level needs evidence, not a date
            if not reported and not ISO.fullmatch((r.get(datecol) or "").strip()):
                errors.append(f"{where}: {datecol} must be YYYY-MM-DD")
            errors += [f"{where}: {c} is empty" for c in required if not (r.get(c) or "").strip()]
            if name == "venue_actions.csv" and (r.get("action_type") or "").strip() == "social" and not re.match(r"https://((www\.)?(instagram|facebook)\.com|chat\.whatsapp\.com|(www\.)?whatsapp\.com/channel)/\S+$", (r.get("url") or "").strip()):
                errors.append(f"{where}: a social link must be an instagram.com, facebook.com, chat.whatsapp.com or whatsapp.com/channel https URL")
            errors += [f"{where}: {c} must be an https link" for c in https if (r.get(c) or "").strip() and not r[c].strip().startswith("https://")]
if errors:
    print("\n".join(errors))
    sys.exit(1)
print("seed evidence check passed")
