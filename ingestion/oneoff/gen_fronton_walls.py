"""Generate `fronton` hitting-wall rows in transform/seeds/manual_walls.csv from Mexico's outdoor fronton-family pins in manual_venues.csv.
Owner 2026-11-22 (ADR 0034 pass 7): traceable, every row confirmation=inferred, access blank. Re-run to pick up new pins; it replaces its own
rows (wall_key prefix 'fronton-wall-') and leaves every other row alone. No outside requests."""
import csv, io
from pathlib import Path

SEEDS = Path(__file__).resolve().parents[2] / "transform" / "seeds"
EVIDENCE = "OpenStreetMap tags only; setting outdoor inferred from leisure=pitch; wall count and access not known"
PREFIX = "fronton-wall-"


def main():
    venues = list(csv.DictReader(open(SEEDS / "manual_venues.csv", encoding="utf-8", newline="")))
    path = SEEDS / "manual_walls.csv"
    with open(path, encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f)
        cols = rd.fieldnames
        keep = [r for r in rd if not r["wall_key"].startswith(PREFIX)]
    new = []
    for v in venues:
        if v["region"] != "MX" or v["setting"] != "outdoor" or not any(k in v["sport"] for k in ("Basque", "Frontenis", "Pelota")):
            continue
        new.append({
            "wall_key": PREFIX + v["venue_key"], "wall_name": v["venue_name"], "city": v["city"], "lat": v["lat"], "lon": v["lon"],
            "location_precision": v["location_precision"], "wall_type": "fronton", "sports_suited": v["sport"],
            "near_venue_name": v["venue_name"], "surface": "", "is_lit": "", "free_to_use": "", "access": "",
            "confirmation": "inferred", "reported_on": v["confirmed_on"], "evidence": EVIDENCE, "region": "MX"})
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, cols, lineterminator="\r\n")
    w.writeheader(); w.writerows(keep + new)
    path.write_bytes(buf.getvalue().encode("utf-8"))
    print(f"{len(new)} fronton wall rows written ({len(keep)} other rows kept)")


if __name__ == "__main__":
    main()
