#!/usr/bin/env python3
"""Claude Code hook: enforce the token- and secret-saving rules from CLAUDE.md without spending tokens on prose.

PreToolUse (Read/Edit/Write/Grep/Bash/browser tools):
  - deny  : reading or editing `.env` (credentials; `.env.example` is fine)
  - deny  : whole-file reads of bulky generated files (app/data/venues.json, *.duckdb, transform/target, transform/logs)
            and of app/index.html (178 KB) without a line range (`limit`)
  - ask   : reading images (screenshots stay in context and are re-read every turn) and taking browser screenshots
UserPromptSubmit:
  - warns once when the session transcript gets large, so the model offers a fresh session (CLAUDE.md: ~150-300k context)

Fails open: any error prints nothing and exits 0, so a bug here can never block work.
Docs: docs/token_efficiency.md. Tune the warning with CC_GUARD_WARN_KB (default 800) and CC_GUARD_REPEAT_KB (default 400).
"""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ENV_FILE_SUFFIX_OK = (".example", ".sample", ".template")
BULKY = re.compile(r"(^|/)(app/data/venues\.json|[^/]*\.duckdb(\.wal)?|transform/(target|logs)/.*)$")
BIG_NEEDS_RANGE = re.compile(r"(^|/)app/index\.html$")
IMAGE = re.compile(r"\.(png|jpe?g|gif|webp|bmp)$")
# `.env` as a whole shell word, optionally with a directory prefix (not `.venv`, `.env.example`, or a regex like `\.env`).
BASH_ENV = re.compile(r"""(?:^|[\s=;|&<>'"(`])(?:[\w.~:-]+[/\\])*\.env(?=$|[\s;|&<>'")`])""")
BASH_BULKY = re.compile(
    r"\b(cat|type|more|less|bat|Get-Content|gc)\b[^|;&\n]*(venues\.json|\.duckdb|transform/(target|logs)/)", re.I
)
BROWSER_COMPUTER = {"mcp__Claude_Browser__computer", "mcp__claude-in-chrome__computer"}
BROWSER_BATCH = {"mcp__Claude_Browser__browser_batch", "mcp__claude-in-chrome__browser_batch"}


def norm(p):
    return str(p or "").replace("\\", "/")


def is_env_file(path):
    name = norm(path).rsplit("/", 1)[-1]
    return name == ".env" or (name.startswith(".env.") and not name.endswith(ENV_FILE_SUFFIX_OK))


def respond(decision, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def pre_tool_use(data):
    tool = data.get("tool_name", "")
    inp = data.get("tool_input") or {}

    if tool in ("Read", "Edit", "Write", "NotebookEdit", "Grep"):
        path = norm(inp.get("file_path") or inp.get("notebook_path") or inp.get("path"))
        if is_env_file(path):
            respond("deny", ".env holds credentials: never read, print or edit it (CLAUDE.md). .env.example lists the keys.")
        if tool in ("Read", "Grep") and BULKY.search(path) and not inp.get("limit") and not inp.get("head_limit"):
            respond("deny", "Bulky generated file: use Grep with a pattern and head_limit, or Read with offset/limit (CLAUDE.md).")
        if tool == "Read":
            if BIG_NEEDS_RANGE.search(path) and not inp.get("limit"):
                respond("deny", "app/index.html is 178 KB: Grep first, then Read a line range with offset and limit (CLAUDE.md).")
            if IMAGE.search(path.lower()):
                respond("ask", "Images stay in context and are re-read every turn. Read this one only if the owner asked.")

    elif tool == "Bash":
        cmd = inp.get("command", "")
        if BASH_ENV.search(cmd):
            respond("deny", "Command touches .env (credentials). Scripts load it themselves; never read or print it (CLAUDE.md).")
        if BASH_BULKY.search(cmd):
            respond("deny", "Don't dump bulky generated files (venues.json, *.duckdb, transform/target, transform/logs). Use grep/head/jq.")

    elif tool in BROWSER_COMPUTER:
        if inp.get("action") == "screenshot":
            respond("ask", "Screenshots cost many tokens. CLAUDE.md: read pages as text (get_page_text/read_page) unless the owner asked.")

    elif tool in BROWSER_BATCH:
        for step in inp.get("actions") or []:
            if (step.get("name") == "computer") and (step.get("input") or {}).get("action") == "screenshot":
                respond("ask", "This batch takes a screenshot. CLAUDE.md: read pages as text unless the owner asked.")


def user_prompt_submit(data):
    transcript = data.get("transcript_path")
    if not transcript or not os.path.exists(transcript):
        return
    kb = os.path.getsize(transcript) // 1024
    warn = int(os.environ.get("CC_GUARD_WARN_KB", "800"))
    repeat = int(os.environ.get("CC_GUARD_REPEAT_KB", "400"))
    state = Path(tempfile.gettempdir()) / f"cc_guard_{re.sub(r'[^A-Za-z0-9_-]', '', str(data.get('session_id', 'x')))}.txt"
    last = int(state.read_text()) if state.exists() else 0
    if kb < warn or (last and kb - last < repeat):
        return
    state.write_text(str(kb))
    msg = (f"Session transcript is about {kb} KB (roughly {kb * 1024 // 4 // 1000}k tokens of history). Every turn re-reads it. "
           "Finish the current step, put the hand-off (what changed, what is next) in the PR description, "
           "and tell the owner to start a fresh session (CLAUDE.md, 'Keeping usage low').")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}))


def main():
    data = json.load(sys.stdin)
    event = data.get("hook_event_name")
    if event == "PreToolUse":
        pre_tool_use(data)
    elif event == "UserPromptSubmit":
        user_prompt_submit(data)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        pass
    sys.exit(0)
