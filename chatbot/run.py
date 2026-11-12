"""Local chatbot prototype: Claude + tools over app/data/venues.json (docs/chatbot.md, layer 2, step 2).

    python chatbot/run.py --ask "Where can I play pickleball in Reno?"
    python chatbot/run.py --questions 1,2,3        # run numbered questions from docs/chatbot.md
    python chatbot/run.py --questions all --budget-usd 0.25

Needs ANTHROPIC_API_KEY (environment or .env; only that one key is read). Writes a transcript with token use and an
estimated cost to chatbot/results/. Stops when the estimated spend passes --budget-usd.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "docs" / "chatbot.md"
RESULTS = Path(__file__).resolve().parent / "results"
DEFAULT_MODEL = "claude-haiku-5-5"
# $ per million tokens (cached prices from the claude-api skill, 2026-10-06; Haiku 5.5 is for prompts up to 100K)
PRICES = {"claude-haiku-5-5": (0.10, 0.50), "claude-sonnet-5-5": (2.0, 10.0), "claude-opus-5-5": (4.0, 20.0)}
MAX_STEPS = 6

SYSTEM = """You are the RacketConnect assistant for racket sports in the places our data covers (California, Nevada, Oregon, Washington, Arizona, New Mexico, Hawaii).

Scope: racket sports (tennis, pickleball, padel, pop tennis, squash, racquetball, badminton, table tennis, beach tennis and the like), places to play or watch them, and where to buy or rent racket-sport gear. For anything else, reply in one or two sentences that you only help with racket sports, courts and gear, and offer a racket-sport alternative. Never write or do the off-topic task.

How to answer:
- Venue, event and wall facts come ONLY from the tools. Never name a venue, event, address, price, opening time or store from memory. If a tool returns nothing, say none were found in our data (that does not prove none exist).
- Repeat the labels the data carries: name basis, "public access not confirmed", confirmation level, inferred address, wall access unknown. Do not call something free or public unless the data says so.
- General questions (what a sport is, rules, how to start, equipment types) can use your own knowledge: say it is general advice, keep it short, and offer to look up places.
- You cannot book, pay or reserve. If asked, say so and point to the venue's own link from the data if there is one.
- Gear: call find_gear. It has no data yet, so say you do not have store or rental data and do not name stores. You may explain what to look for in a racket.
- Pad is not padel: padel is a walled glass court; pop tennis (paddle tennis) is an open court with a low net. Do not mix them up.
- If the user states their sport, city or level, call save_profile. Use the saved profile below when they leave out sport or city.
- Several results can share a name (chain branches are separate places). Use each result's display_name so they can be told apart.
- Be concise: a short answer, at most 5 venues, one line each (name, city, what the data says about access). No tables.
"""


def load_key() -> str | None:
    import os
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    env = ROOT / ".env"
    if env.exists():
        from dotenv import dotenv_values
        return dotenv_values(env).get("ANTHROPIC_API_KEY") or None
    return None


def read_questions() -> dict[int, tuple[str, str]]:
    out = {}
    in_questions = False  # docs/chatbot.md also holds the plan and UX todo: read only the test-questions section
    for line in QUESTIONS.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_questions = line.startswith("## Chatbot test questions")
        if not in_questions:
            continue
        m = re.match(r"^(\d+)\.\s+(.*)$", line)
        if m:
            q, _, expect = m.group(2).partition(" Expect:")
            out[int(m.group(1))] = (q.strip(), expect.strip())
    return out


def cost(model: str, usage) -> float:
    pin, pout = PRICES.get(model, (4.0, 20.0))
    cin = usage["in"] + usage["cache_write"] * 1.25 + usage["cache_read"] * 0.1
    return (cin * pin + usage["out"] * pout) / 1e6


def ask(client, model: str, question: str, usage: dict, log: list[str]) -> str:
    profile = tools.load_profile()
    system = [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}},
              {"type": "text", "text": f"Data generated {tools.data()['meta']['generated']}. Today is {datetime.now():%Y-%m-%d}. "
                                       f"Saved profile: {profile or 'none'}."}]
    messages = [{"role": "user", "content": question}]
    for _ in range(MAX_STEPS):
        r = client.messages.create(model=model, max_tokens=3000, system=system, tools=tools.TOOL_DEFS, messages=messages,
                                   output_config={"effort": "low"})
        u = r.usage
        usage["in"] += u.input_tokens
        usage["out"] += u.output_tokens
        usage["cache_write"] += getattr(u, "cache_creation_input_tokens", 0) or 0
        usage["cache_read"] += getattr(u, "cache_read_input_tokens", 0) or 0
        if r.stop_reason == "refusal":
            return "[model refused]"
        calls = [b for b in r.content if b.type == "tool_use"]
        if r.stop_reason != "tool_use" or not calls:
            if r.stop_reason == "max_tokens":
                log.append("(hit max_tokens)")
            return "".join(b.text for b in r.content if b.type == "text").strip()
        messages.append({"role": "assistant", "content": r.content})
        results = []
        for c in calls:
            res = tools.call(c.name, c.input)
            log.append(f"tool {c.name}({c.input}) -> {str(res)[:160]}")
            results.append({"type": "tool_result", "tool_use_id": c.id, "content": __import__("json").dumps(res, ensure_ascii=False)})
        messages.append({"role": "user", "content": results})  # all results in one message
    return "[stopped: too many tool steps]"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ask")
    ap.add_argument("--questions", help="comma list of numbers from docs/chatbot.md, or 'all'")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--budget-usd", type=float, default=0.25)
    a = ap.parse_args()
    if not a.ask and not a.questions:
        ap.error("give --ask or --questions")
    key = load_key()
    if not key:
        print("No ANTHROPIC_API_KEY (set it in the environment or add it to .env). Nothing was sent.", file=sys.stderr)
        return 2
    import anthropic
    client = anthropic.Anthropic(api_key=key)

    jobs: list[tuple[str, str, str]] = []
    if a.ask:
        jobs.append(("ask", a.ask, ""))
    if a.questions:
        qs = read_questions()
        nums = sorted(qs) if a.questions == "all" else [int(x) for x in a.questions.split(",")]
        jobs += [(str(n), qs[n][0], qs[n][1]) for n in nums]

    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / f"{datetime.now():%Y%m%d-%H%M%S}.md"
    total = 0.0
    lines = [f"# Chatbot prototype run, model {a.model}\n"]
    for tag, q, expect in jobs:
        usage = {"in": 0, "out": 0, "cache_write": 0, "cache_read": 0}
        log: list[str] = []
        try:
            ans = ask(client, a.model, q, usage, log)
        except anthropic.APIError as e:
            ans = f"[API error: {e}]"
        c = cost(a.model, usage)
        total += c
        print(f"\n== {tag}: {q}\n{ans}\n(~${c:.4f}, in {usage['in']} out {usage['out']})")
        lines += [f"## {tag}. {q}", f"Expect: {expect}" if expect else "", "", "Tools:", *[f"- {x}" for x in log], "", "Answer:", ans, "",
                  f"Tokens in {usage['in']} (cache write {usage['cache_write']}, read {usage['cache_read']}), out {usage['out']}, ~${c:.4f}", ""]
        if total >= a.budget_usd:
            print(f"\nBudget ${a.budget_usd} reached (~${total:.4f}); stopping.")
            lines.append(f"Stopped: budget ${a.budget_usd} reached.")
            break
    lines.append(f"\nTotal ~${total:.4f} for {len(jobs)} question(s) max.")
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nTranscript: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
