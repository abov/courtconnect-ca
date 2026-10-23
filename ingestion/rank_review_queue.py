"""Rank the sport review queue so each review session starts with the clear-cut cases.

    python ingestion/rank_review_queue.py        (or: make rank-review)

Queue: marts.mart_sport_evidence where needs_review (a sport label resting only on a business-name word or a loose OSM tag).
Labels: the human confirm/reject rows in transform/seeds/place_sport_overrides.csv.
Model: a small logistic regression over simple clues (sport, Overture category, name words, website domain, store words,
distance to the nearest OSM court). It only ORDERS the queue; a person still checks the venue's own page and writes the
verdict in place_sport_overrides.csv. Its guess is never shown on the map.

Writes docs/review_priority.csv (most clear-cut first) and prints a leave-one-out check of how often the guess was right.
Needs scikit-learn: pip install -r requirements-ml.txt
"""
from __future__ import annotations

import re
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import LeaveOneOut, cross_val_predict

DB = Path("courtconnect.duckdb")
OUT = Path("docs/review_priority.csv")
STORE_WORDS = {"warehouse", "direct", "gear", "gearbox", "store", "shop", "supply", "outlet", "pro shop", "apparel", "equipment"}
LIKELY = 0.7   # p(confirm) at or above -> likely_confirm; at or below 1 - LIKELY -> likely_reject


def words(text: str | None) -> list[str]:
    return re.findall(r"[a-z]+", (text or "").lower())


def nearest_m(lat: np.ndarray, lon: np.ndarray, clat: np.ndarray, clon: np.ndarray) -> np.ndarray:
    """Distance in metres from each point to the nearest OSM court (haversine)."""
    out = np.full(len(lat), np.inf)
    rc_lat, rc_lon = np.radians(clat), np.radians(clon)
    for i, (a, b) in enumerate(zip(lat, lon)):
        if np.isnan(a) or np.isnan(b):
            continue
        ra, rb = np.radians(a), np.radians(b)
        h = np.sin((rc_lat - ra) / 2) ** 2 + np.cos(ra) * np.cos(rc_lat) * np.sin((rc_lon - rb) / 2) ** 2
        out[i] = (2 * 6_371_000 * np.arcsin(np.sqrt(h))).min()
    return out


def features(row: pd.Series, sports: list[str]) -> dict:
    sport = row["sport_name"]
    sport_words = set(words(sport))
    name_words = words(row["name"])
    name = " ".join(name_words)
    phrase = " ".join(words(sport))
    domain = (row["website_domain"] or "").lower()
    category = row["category"] or "none"
    f: dict = {f"sport={sport}": 1, f"category={category}": 1}
    # name words other than the sport's own (e.g. "club", "academy", "beach", "warehouse")
    for w in set(name_words) - sport_words:
        f[f"word={w}"] = 1
    # the sport's name contains another sport's name (Beach Tennis, Street Tennis, Real Tennis): place names often fake these
    f["sport_contains_other_sport"] = int(any(o != sport and re.search(rf"\b{re.escape(o.lower())}\b", sport.lower()) for o in sports))
    f["name_starts_with_sport"] = int(name.startswith(phrase))
    f["store_category"] = int("store" in category or "shop" in category)
    f["store_word"] = int(any(s in name or s in domain for s in STORE_WORDS))
    f["has_website"] = int(bool(domain))
    f["domain_has_sport"] = int(bool(domain) and phrase.replace(" ", "") in domain.replace("-", ""))
    f["gov_domain"] = int(domain.endswith(".gov") or ".ca.us" in domain or ".nv.us" in domain)
    d = row["osm_court_m"]
    f["osm_court_within_100m"] = int(d <= 100)
    f["osm_court_within_500m"] = int(d <= 500)
    f["loose_osm_tag"] = int(row["best_rung_label"] == "osm_tag_loose")
    return f


def main() -> None:
    con = duckdb.connect(str(DB), read_only=True)
    sports = [r[0] for r in con.execute("select sport_name from core.dim_sport").fetchall()]

    labels = con.execute("""
        select o.place_id, null as venue_id, trim(o.sport) as sport_name, lower(trim(o.verdict)) as verdict,
               p.place_name as name, p.category, p.website_domain, p.lat, p.lon, 'name_keyword' as best_rung_label
        from raw.place_sport_overrides o
        join core.dim_place p on p.place_id = o.place_id
    """).df()

    # one row per queued (venue, sport); use the place whose name gave the sport when there is one
    queue = con.execute("""
        with q as (
            select e.venue_id, e.sport_id, e.sport_name, e.best_rung_label
            from marts.mart_sport_evidence e where e.needs_review
        ),
        pick as (
            select q.venue_id, q.sport_id, p.place_id, p.place_name, p.category, p.website_domain, p.lat, p.lon,
                   row_number() over (partition by q.venue_id, q.sport_id
                                      order by (b.match_type = 'name_keyword') desc nulls last, p.place_id) as rn
            from q
            join core.dim_place p on p.venue_id = q.venue_id
            left join core.bridge_place_sport b on b.place_id = p.place_id and b.sport_id = q.sport_id
        )
        select q.venue_id, k.place_id, q.sport_name, q.best_rung_label, v.venue_name, v.city, v.region,
               coalesce(k.place_name, v.venue_name) as name, k.category, k.website_domain,
               coalesce(k.lat, v.lat) as lat, coalesce(k.lon, v.lon) as lon
        from q
        join core.dim_venue v on v.venue_id = q.venue_id
        left join pick k on k.venue_id = q.venue_id and k.sport_id = q.sport_id and k.rn = 1
    """).df()

    courts = con.execute("select lat, lon from staging.stg_osm_courts where lat is not null").df()
    for df in (labels, queue):
        df["osm_court_m"] = nearest_m(df["lat"].to_numpy(float), df["lon"].to_numpy(float),
                                      courts["lat"].to_numpy(float), courts["lon"].to_numpy(float))
        # a loose-OSM-tag row's own location IS an OSM court, so its distance says nothing; blank it
        df.loc[df["best_rung_label"] == "osm_tag_loose", "osm_court_m"] = np.inf

    vec = DictVectorizer()
    X = vec.fit_transform([features(r, sports) for _, r in labels.iterrows()])
    y = (labels["verdict"] == "confirm").astype(int).to_numpy()
    model = LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000)

    # honesty check: predict each label with a model that never saw it
    p_loo = cross_val_predict(model, X, y, cv=LeaveOneOut(), method="predict_proba")[:, 1]
    sure = (p_loo >= LIKELY) | (p_loo <= 1 - LIKELY)
    print(f"labels: {len(y)} ({y.sum()} confirm, {len(y) - y.sum()} reject)")
    print(f"leave-one-out: accuracy {((p_loo >= 0.5) == y).mean():.0%}, AUC {roc_auc_score(y, p_loo):.2f}; "
          f"'likely' calls {sure.sum()} of {len(y)}, right {((p_loo[sure] >= 0.5) == y[sure]).mean():.0%}")
    wrong = labels.loc[(p_loo >= 0.5) != y, ["name", "sport_name", "verdict"]]
    if len(wrong):
        print("missed:", "; ".join(f"{r.name} / {r.sport_name} ({r.verdict})" for r in wrong.itertuples()))

    model.fit(X, y)
    Xq = vec.transform([features(r, sports) for _, r in queue.iterrows()])
    p = model.predict_proba(Xq)[:, 1]
    names = np.array(vec.get_feature_names_out())
    contrib = Xq.multiply(model.coef_[0]).toarray()

    def reasons(i: int) -> str:
        c = contrib[i]
        top = np.argsort(-np.abs(c))[:3]
        return "; ".join(f"{names[j]} ({'+' if c[j] > 0 else '-'})" for j in top if c[j] != 0)

    queue["p_confirm"] = p.round(2)
    queue["model_guess"] = np.where(p >= LIKELY, "likely_confirm", np.where(p <= 1 - LIKELY, "likely_reject", "unclear"))
    queue["reasons"] = [reasons(i) for i in range(len(queue))]
    queue["certainty"] = np.abs(p - 0.5)
    # a site already flagged dead (parked, hijacked, expired, no DNS) cannot settle the sport: sort those rows last
    dead = {d for (d,) in con.execute("select lower(domain) from staging.stg_website_checks where status = 'dead'").fetchall()}
    queue["website_status"] = np.where(queue["website_domain"].fillna("").str.lower().isin(dead), "dead", "")
    queue = queue.sort_values(["website_status", "certainty", "venue_name"], ascending=[True, False, True]).reset_index(drop=True)
    queue["review_priority"] = queue.index + 1
    cols = ["review_priority", "model_guess", "p_confirm", "sport_name", "venue_name", "name", "city", "region",
            "category", "website_domain", "website_status", "best_rung_label", "reasons", "venue_id", "place_id"]
    queue[cols].rename(columns={"name": "place_name"}).to_csv(OUT, index=False, lineterminator="\r\n")
    print(f"queue: {len(queue)} rows -> {OUT}  " + ", ".join(f"{k} {v}" for k, v in queue["model_guess"].value_counts().items())
          + f"; {(queue['website_status'] == 'dead').sum()} with a dead site sorted last")


if __name__ == "__main__":
    main()
