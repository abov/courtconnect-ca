"""Live view of agent activity: what every Claude Code session on this machine is doing right now.

Tails this machine's session logs (~/.claude/projects/*courtconnect*/**/*.jsonl) and serves a small page
at http://127.0.0.1:8766 that updates every 2 seconds: one card per session (state, turns, tokens, errors,
tool mix) and a time-ordered feed of tool calls (tool, target, how long, failed or not).

Local and read-only: binds to 127.0.0.1, sends nothing anywhere, writes nothing. It shows tool names and short
targets only, never prompts, replies or file contents; secrets-looking values in commands are masked and `.env`
is shown as [env]. Cloud routines and other machines have no logs here, so they do not appear.

  python ingestion/agent_activity.py                 # last 6 hours, port 8766
  python ingestion/agent_activity.py --hours 24 --port 9000 --all-projects
"""
from __future__ import annotations

import argparse
import json
import re
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE = Path.home() / ".claude" / "projects"
MAX_EVENTS = 6000
SECRET_RE = re.compile(r"(?i)((?:token|key|secret|password|passwd|auth\w*|bearer)\s*[=: ]\s*)\S+")
ENV_RE = re.compile(r"(?<![\w.-])\.env(?![\w.-]|\.example)")


class State:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.events: list[dict] = []
        self.seq = 0
        self.sessions: dict[str, dict] = {}
        self.pending: dict[str, dict] = {}  # tool_use id -> event
        self.offsets: dict[Path, int] = {}


STATE = State()


def parse_ts(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def clean(s: str, n: int = 110) -> str:
    s = SECRET_RE.sub(r"\1***", s.strip().splitlines()[0] if s.strip() else "")
    s = ENV_RE.sub("[env]", s)
    return s if len(s) <= n else s[: n - 1] + "…"


def short_path(p: str) -> str:
    p = p.replace("\\", "/")
    if p.rsplit("/", 1)[-1] == ".env":
        return "[env]"
    for marker in ("/worktrees/", "/courtconnect-ca/"):
        if marker in p:
            tail = p.split(marker, 1)[1]
            return tail.split("/", 1)[1] if marker == "/worktrees/" and "/" in tail else tail
    return p[-70:]


def describe(name: str, inp: dict) -> str:
    if name == "Bash" or name == "PowerShell":
        return clean(inp.get("command") or "")
    if name in ("Read", "Edit", "Write", "NotebookEdit"):
        return short_path(inp.get("file_path") or inp.get("notebook_path") or "")
    if name in ("Grep", "Glob"):
        return clean(inp.get("pattern") or "", 70)
    if name == "WebFetch":
        m = re.match(r"https?://([^/]+)", inp.get("url") or "")
        return m.group(1) if m else ""
    if name == "WebSearch":
        return clean(inp.get("query") or "", 70)
    if name in ("Agent", "Task"):
        return clean(inp.get("description") or "", 70)
    return ""


def session(sid: str, proj: str) -> dict:
    s = STATE.sessions.get(sid)
    if s is None:
        s = STATE.sessions[sid] = {
            "id": sid, "proj": proj, "first": 0.0, "last": 0.0, "turns": 0, "calls": 0, "errors": 0,
            "out": 0, "fresh": 0, "peak": 0, "tools": {}, "lastTool": "",
        }
    return s


def add_event(ev: dict) -> None:
    STATE.seq += 1
    ev["seq"] = STATE.seq
    STATE.events.append(ev)
    if len(STATE.events) > MAX_EVENTS:
        del STATE.events[: len(STATE.events) - MAX_EVENTS]


def ingest(path: Path, proj: str, line: str, cutoff: float) -> None:
    try:
        o = json.loads(line)
    except ValueError:
        return
    msg = o.get("message")
    if not isinstance(msg, dict) or not o.get("timestamp"):
        return
    when = parse_ts(o["timestamp"])
    if when < cutoff:
        return
    sid = o.get("sessionId") or path.stem
    s = session(sid, proj)
    s["first"] = min(s["first"] or when, when)
    s["last"] = max(s["last"], when)
    content = msg.get("content")
    if o.get("type") == "assistant":
        u = msg.get("usage")
        mid = msg.get("id")
        if u and mid and mid not in s.setdefault("_mids", set()):
            s["_mids"].add(mid)
            s["turns"] += 1
            s["out"] += u.get("output_tokens", 0)
            s["fresh"] += u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
            ctx = u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
            s["peak"] = max(s["peak"], ctx)
        for b in content if isinstance(content, list) else []:
            if b.get("type") != "tool_use":
                continue
            name = b.get("name", "?")
            short = name.split("__")[-1] if name.startswith("mcp__") else name
            ev = {"t": when, "sid": sid, "proj": proj, "tool": short, "detail": describe(name, b.get("input") or {}),
                  "ms": None, "err": False}
            add_event(ev)
            STATE.pending[b["id"]] = ev
            s["calls"] += 1
            s["lastTool"] = short
            s["tools"][short] = s["tools"].get(short, 0) + 1
    elif o.get("type") == "user" and isinstance(content, list):
        for b in content:
            if b.get("type") != "tool_result":
                continue
            ev = STATE.pending.pop(b.get("tool_use_id"), None)
            if ev is None:
                continue
            ev["ms"] = int(max(0.0, when - ev["t"]) * 1000)
            if b.get("is_error"):
                ev["err"] = True
                s["errors"] += 1
            STATE.seq += 1
            ev["seq"] = STATE.seq  # re-announce the finished call so polling clients refresh it


def scan(args: argparse.Namespace) -> None:
    cutoff = time.time() - args.hours * 3600
    dirs = [d for d in BASE.glob("*") if d.is_dir() and (args.all_projects or "courtconnect" in d.name)]
    for d in dirs:
        proj = d.name.split("worktrees-")[-1][:34]
        for f in d.rglob("*.jsonl"):
            try:
                st = f.stat()
            except OSError:
                continue
            off = STATE.offsets.get(f, 0)
            if st.st_mtime < cutoff and off == 0:
                continue
            if st.st_size <= off:
                continue
            with f.open("rb") as fh:
                fh.seek(off)
                data = fh.read()
            end = data.rfind(b"\n")
            if end < 0:
                continue  # partial line, wait for the rest
            STATE.offsets[f] = off + end + 1
            with STATE.lock:
                for line in data[: end + 1].decode("utf-8", errors="replace").splitlines():
                    ingest(f, proj, line, cutoff)


def tail_loop(args: argparse.Namespace) -> None:
    while True:
        try:
            scan(args)
        except Exception as e:  # keep serving whatever we have
            print("scan error:", e)
        time.sleep(1.0)


def snapshot(after: int, sid: str | None) -> dict:
    now = time.time()
    with STATE.lock:
        sess = []
        for s in STATE.sessions.values():
            age = now - s["last"]
            state = "active" if age < 90 else "idle" if age < 900 else "done"
            top = sorted(s["tools"].items(), key=lambda kv: -kv[1])[:5]
            sess.append({**{k: v for k, v in s.items() if not k.startswith("_") and k != "tools"},
                         "state": state, "age": age, "top": top})
        sess.sort(key=lambda x: x["last"], reverse=True)
        evs = [e for e in STATE.events if e["seq"] > after and (not sid or e["sid"] == sid)]
        return {"now": now, "seq": STATE.seq, "sessions": sess, "events": evs[-400:]}


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent Activity</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1c2330;--mut:#6b7686;--line:#e2e6ec;--ok:#1a7f4b;--idle:#b7791f;--done:#8a94a3;--err:#c0392b;--acc:#2563eb}
@media (prefers-color-scheme:dark){:root{--bg:#10141b;--card:#171c26;--ink:#e6eaf1;--mut:#8b96a8;--line:#262d3b;--ok:#4cc38a;--idle:#e0a94a;--done:#7a8496;--err:#ff6b5e;--acc:#6ea0ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.4 system-ui,Segoe UI,sans-serif}
header{display:flex;gap:12px;align-items:center;padding:12px 16px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:2;flex-wrap:wrap}
h1{font-size:16px;margin:0}.mut{color:var(--mut)}button{background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:6px;padding:4px 10px;cursor:pointer}
main{padding:16px;max-width:1200px;margin:0 auto}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:10px;margin-bottom:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px;cursor:pointer}
.card.sel{outline:2px solid var(--acc)}.card b{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px;background:var(--done)}
.active .dot{background:var(--ok);animation:p 1.4s infinite}.idle .dot{background:var(--idle)}
@keyframes p{50%{opacity:.35}}.row2{display:flex;gap:10px;flex-wrap:wrap;font-size:12px;color:var(--mut);margin-top:4px}
.err{color:var(--err)}h2{font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);margin:0 0 6px}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:8px;overflow:hidden}
td{padding:5px 9px;border-bottom:1px solid var(--line);vertical-align:top}tr:last-child td{border-bottom:0}
td.t,td.ms{white-space:nowrap;color:var(--mut);font-variant-numeric:tabular-nums}td.tool{white-space:nowrap;font-weight:600}
td.d{word-break:break-all;font-family:ui-monospace,Consolas,monospace;font-size:12.5px}tr.e td.tool{color:var(--err)}
@media (max-width:600px){td.s{display:none}}
</style></head><body>
<header><h1>Agent Activity</h1><span class="mut" id="sum">connecting…</span>
<span style="flex:1"></span><span class="mut" id="filt"></span><button id="pause">Pause</button></header>
<main><h2>Sessions (click one to filter)</h2><div class="cards" id="cards"></div>
<h2>Tool calls, newest first</h2><table><tbody id="feed"></tbody></table></main>
<script>
let after=0,sel=null,paused=false,events=[],ids={};
const $=id=>document.getElementById(id);
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const fmtK=n=>n>=1e3?(n/1e3).toFixed(0)+'k':n;
const ago=s=>s<60?Math.round(s)+'s ago':s<3600?Math.round(s/60)+'m ago':(s/3600).toFixed(1)+'h ago';
$('pause').onclick=()=>{paused=!paused;$('pause').textContent=paused?'Resume':'Pause'};
async function tick(){
  if(paused)return;
  try{
    const r=await fetch('/api/state?after='+after+(sel?'&sid='+sel:''));const d=await r.json();
    after=d.seq;
    for(const e of d.events){const i=ids[e.sid+e.t+e.tool+e.detail];if(i!==undefined)events[i]=e;else{ids[e.sid+e.t+e.tool+e.detail]=events.length;events.push(e)}}
    if(events.length>800){events=events.slice(-600);ids={};events.forEach((e,i)=>ids[e.sid+e.t+e.tool+e.detail]=i)}
    const act=d.sessions.filter(s=>s.state==='active').length;
    $('sum').textContent=act+' active · '+d.sessions.length+' sessions · updated '+new Date().toLocaleTimeString();
    $('cards').innerHTML=d.sessions.map(s=>`<div class="card ${s.state} ${sel===s.id?'sel':''}" data-id="${s.id}">
      <b><span class="dot"></span>${esc(s.proj)}</b>
      <div class="row2"><span>${s.state} · ${ago(s.age)}</span><span>${s.id.slice(0,8)}</span></div>
      <div class="row2"><span>${s.turns} turns</span><span>${s.calls} calls</span><span class="${s.errors?'err':''}">${s.errors} errors</span><span>ctx peak ${fmtK(s.peak)}</span></div>
      <div class="row2"><span>${s.top.map(t=>esc(t[0])+' '+t[1]).join(' · ')}</span></div></div>`).join('');
    document.querySelectorAll('.card').forEach(c=>c.onclick=()=>{sel=sel===c.dataset.id?null:c.dataset.id;after=0;events=[];ids={};$('filt').textContent=sel?'filtered: '+sel.slice(0,8):'';tick()});
    const names={};d.sessions.forEach(s=>names[s.id]=s.proj);
    $('feed').innerHTML=events.slice().sort((a,b)=>b.t-a.t).slice(0,300).map(e=>`<tr class="${e.err?'e':''}">
      <td class="t">${new Date(e.t*1000).toLocaleTimeString()}</td><td class="tool">${esc(e.tool)}${e.err?' ✗':''}</td>
      <td class="d">${esc(e.detail)}</td><td class="ms">${e.ms==null?'…':e.ms<1000?e.ms+'ms':(e.ms/1000).toFixed(1)+'s'}</td>
      <td class="s mut">${esc((names[e.sid]||e.proj).slice(0,22))}</td></tr>`).join('');
  }catch(x){$('sum').textContent='server not reachable'}
}
tick();setInterval(tick,2000);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a) -> None:  # quiet
        pass

    def do_GET(self) -> None:
        u = urlparse(self.path)
        if u.path == "/api/state":
            q = parse_qs(u.query)
            body = json.dumps(snapshot(int(q.get("after", ["0"])[0]), (q.get("sid") or [None])[0])).encode()
            ctype = "application/json"
        elif u.path in ("/", "/index.html"):
            body, ctype = PAGE.encode(), "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hours", type=float, default=6, help="how far back to read at start (default 6)")
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--all-projects", action="store_true", help="include Claude Code projects other than courtconnect")
    args = ap.parse_args()
    scan(args)
    threading.Thread(target=tail_loop, args=(args,), daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Agent activity: http://127.0.0.1:{args.port}  ({len(STATE.sessions)} sessions in the last {args.hours:g}h; Ctrl+C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
