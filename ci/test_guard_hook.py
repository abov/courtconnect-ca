"""Checks the Claude Code guard hook (.claude/hooks/guard.py): what it denies, asks about and lets through.
Run: python ci/test_guard_hook.py   (no dependencies; exits 1 on any mismatch)"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "guard.py"


def run(payload):
    p = subprocess.run([sys.executable, "-I", str(HOOK)], input=json.dumps(payload), capture_output=True, text=True,
                       env={**os.environ, "CC_GUARD_WARN_KB": "1", "CC_GUARD_REPEAT_KB": "1"})
    assert p.returncode == 0, p.stderr
    if not p.stdout.strip():
        return "allow"
    out = json.loads(p.stdout)["hookSpecificOutput"]
    return out.get("permissionDecision", "context")


def pre(tool, **inp):
    return run({"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": inp})


CASES = [
    (pre("Read", file_path="C:/dev/x/.env"), "deny"),
    (pre("Read", file_path="C:\\dev\\x\\.env.local"), "deny"),
    (pre("Edit", file_path=".env", old_string="a", new_string="b"), "deny"),
    (pre("Read", file_path="C:/dev/x/.env.example"), "allow"),
    (pre("Read", file_path="C:/dev/x/app/data/venues.json"), "deny"),
    (pre("Read", file_path="C:/dev/x/app/data/venues.json", limit=5), "allow"),
    (pre("Read", file_path="transform/target/run_results.json"), "deny"),
    (pre("Read", file_path="courtconnect.duckdb"), "deny"),
    (pre("Read", file_path="C:/dev/x/app/index.html"), "deny"),
    (pre("Read", file_path="C:/dev/x/app/index.html", offset=10, limit=40), "allow"),
    (pre("Read", file_path="docs/screenshots/map.png"), "ask"),
    (pre("Read", file_path="docs/status.md"), "allow"),
    (pre("Grep", pattern="x", path="app/data/venues.json"), "deny"),
    (pre("Grep", pattern="x", path="app/data/venues.json", head_limit=5), "allow"),
    (pre("Grep", pattern="x", path="docs"), "allow"),
    (pre("Bash", command="cat .env"), "deny"),
    (pre("Bash", command="grep KEY ../../.env | head"), "deny"),
    (pre("Bash", command="cat .env.example"), "allow"),
    (pre("Bash", command=".venv/Scripts/dbt build --project-dir transform"), "allow"),
    (pre("Bash", command="grep -n \"\\.env\" ingestion/x.py"), "allow"),
    (pre("Bash", command="cat app/data/venues.json"), "deny"),
    (pre("Bash", command="head -c 500 app/data/venues.json"), "allow"),
    (pre("mcp__Claude_Browser__computer", action="screenshot"), "ask"),
    (pre("mcp__Claude_Browser__computer", action="left_click"), "allow"),
    (pre("mcp__Claude_Browser__browser_batch", actions=[{"name": "computer", "input": {"action": "screenshot"}}]), "ask"),
    (pre("mcp__Claude_Browser__browser_batch", actions=[{"name": "navigate", "input": {"url": "x"}}]), "allow"),
]

with tempfile.TemporaryDirectory() as d:
    big = Path(d) / "t.jsonl"
    big.write_bytes(b"x" * 4096)
    sid = "guardtest" + str(os.getpid())
    first = run({"hook_event_name": "UserPromptSubmit", "transcript_path": str(big), "session_id": sid})
    again = run({"hook_event_name": "UserPromptSubmit", "transcript_path": str(big), "session_id": sid})
    (Path(tempfile.gettempdir()) / f"cc_guard_{sid}.txt").unlink(missing_ok=True)
    CASES += [(first, "context"), (again, "allow")]
    CASES.append((run({"hook_event_name": "UserPromptSubmit", "transcript_path": "missing.jsonl"}), "allow"))
CASES.append((run({"hook_event_name": "PreToolUse"}), "allow"))

bad = [(i, got, want) for i, (got, want) in enumerate(CASES) if got != want]
for i, got, want in bad:
    print(f"case {i}: got {got}, want {want}")
print("guard hook: all", len(CASES), "cases pass" if not bad else "cases ran, FAILED")
sys.exit(1 if bad else 0)
