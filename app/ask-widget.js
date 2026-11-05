// RacketConnect ask box as a pop-up on the map page (ADR 0033, layer 1: rule-based, no AI model, no server).
// AskWidget.mount(data) adds a launcher button and a small chat panel; answers come from ask.js over the venues data already loaded.
(function (root) {
  "use strict";
  const CSS = `
  #askfab { position: fixed; right: 16px; bottom: 40px; z-index: 4; display: flex; align-items: center; gap: 6px; padding: 10px 16px; border: 0; border-radius: var(--r-pill, 999px); background: var(--accent); color: var(--on-accent); font: 700 14px/1 var(--font-head, system-ui); box-shadow: var(--shadow); cursor: pointer; }
  #askfab:focus-visible, #askpanel button:focus-visible, #askpanel input:focus-visible { outline: 3px solid var(--hi, #F2B134); outline-offset: 2px; }
  #askpanel { position: fixed; right: 16px; bottom: 40px; z-index: 7; width: min(380px, calc(100vw - 32px)); height: min(540px, calc(100dvh - 120px)); display: flex; flex-direction: column; background: var(--panel); color: var(--text); border: 1px solid var(--line); border-radius: var(--r-md, 12px); box-shadow: var(--shadow); overflow: hidden; }
  #askpanel[hidden] { display: none; }
  #askpanel header { display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; }
  #askpanel h2 { margin: 0; font: 800 16px/1.2 var(--font-head, system-ui); color: var(--accent); }
  #askclose { border: 0; background: none; color: var(--muted); font-size: 22px; line-height: 1; padding: 4px 8px; cursor: pointer; }
  #asklog { flex: 1; overflow-y: auto; padding: 10px 12px; display: flex; flex-direction: column; gap: 10px; }
  #askpanel .am { background: var(--bg); border: 1px solid var(--line); border-radius: var(--r-md, 12px); padding: 10px; font-size: 14px; }
  #askpanel .am.me { align-self: flex-end; background: var(--accent); color: var(--on-accent); border-color: var(--accent); max-width: 85%; }
  #askpanel .am p { margin: 0 0 6px; } #askpanel .am p:last-child { margin: 0; }
  #askpanel .am.note { color: var(--muted); font-size: 13px; }
  #askpanel .ai { border-top: 1px solid var(--line); padding-top: 6px; margin-top: 6px; }
  #askpanel .ai b { display: block; } #askpanel .ai span { color: var(--muted); font-size: 13px; }
  #askpanel .ai a { color: var(--accent); }
  .askchips { display: flex; flex-wrap: wrap; gap: 6px; }
  .askchips button { font: inherit; font-size: 13px; padding: 5px 10px; border-radius: var(--r-pill, 999px); border: 1px solid var(--line); background: var(--chip); color: var(--text); cursor: pointer; }
  #askform { display: flex; gap: 8px; padding: 10px 12px; border-top: 1px solid var(--line); }
  #askq { flex: 1; min-width: 0; font: inherit; font-size: 16px; padding: 8px 10px; border-radius: var(--r-sm, 8px); border: 1px solid var(--line); background: var(--bg); color: var(--text); }
  #askform button { font: 700 14px var(--font-head, system-ui); padding: 8px 14px; border: 0; border-radius: var(--r-sm, 8px); background: var(--accent); color: var(--on-accent); cursor: pointer; }
  @media (max-width: 800px) {
    #askfab { right: auto; left: 12px; bottom: calc(58vh + 12px); bottom: calc(58dvh + 12px); top: auto; }   /* phones: the map is the top 42dvh, so sit at its bottom-left */
    #askpanel { left: 0; right: 0; bottom: 0; width: auto; height: 70dvh; border-radius: var(--r-md, 12px) var(--r-md, 12px) 0 0; padding-bottom: env(safe-area-inset-bottom); }
  }
  @media (pointer: coarse) { #askfab, .askchips button, #askform button, #askclose { min-height: 44px; } }`;

  function el(tag, attrs, text) {
    const e = document.createElement(tag);
    for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (text) e.textContent = text;
    return e;
  }

  function mount(data, ctx) {
    if (document.getElementById("askfab") || !root.Ask) return;
    const store = {
      get() { try { return JSON.parse(localStorage.getItem("cc_ask_profile") || "{}"); } catch (e) { return {}; } },
      set(v) { try { localStorage.setItem("cc_ask_profile", JSON.stringify(v)); } catch (e) {} },
      clear() { try { localStorage.removeItem("cc_ask_profile"); } catch (e) {} }
    };
    const ask = root.Ask.create(data, store);
    document.head.appendChild(el("style", {}, CSS));

    const fab = el("button", {id: "askfab", type: "button", "aria-expanded": "false", "aria-controls": "askpanel"}, "Ask");
    fab.insertAdjacentText("afterbegin", "\u{1F4AC} ");
    const panel = el("aside", {id: "askpanel", role: "dialog", "aria-label": "Ask RacketConnect", hidden: ""});
    const head = el("header");
    head.append(el("h2", {}, "Ask RacketConnect"));
    const close = el("button", {id: "askclose", type: "button", "aria-label": "Close"}, "×");
    head.append(close);
    const log = el("div", {id: "asklog", "aria-live": "polite"});
    const form = el("form", {id: "askform"});
    const input = el("input", {id: "askq", autocomplete: "off", placeholder: "e.g. pickleball in Reno", "aria-label": "Your question"});
    form.append(input, el("button", {}, "Ask"));
    panel.append(head, log, form);
    document.body.append(fab, panel);

    function add(node) { log.appendChild(node); node.scrollIntoView({block: "end"}); }
    function render(r) {
      const m = el("div", {class: "am"});
      r.lines.filter(Boolean).forEach(l => m.appendChild(el("p", {}, l)));
      (r.items || []).forEach(it => {
        const d = el("div", {class: "ai"});
        d.appendChild(el("b", {}, it.title)); d.appendChild(el("span", {}, it.detail));
        if (it.url && /^https?:\/\//.test(it.url)) { const a = el("a", {href: it.url, target: "_blank", rel: "noopener noreferrer"}, " Open link"); d.appendChild(a); }
        m.appendChild(d);
      });
      add(m);
      if (r.chips && r.chips.length) addChips(r.chips);
    }
    // tappable next steps; only the newest row stays, so the log doesn't fill with stale buttons
    function addChips(list) {
      const chips = el("div", {class: "askchips"});
      list.forEach(t => { const b = el("button", {type: "button"}, t); b.addEventListener("click", () => go(t)); chips.appendChild(b); });
      add(chips);
    }
    function go(q) {
      if (!q.trim()) return;
      log.querySelectorAll(".askchips").forEach(n => n.remove());
      add(el("div", {class: "am me"}, q)); render(ask.answer(q, ctx));
    }

    function intro() {
      add(el("div", {class: "am note"}, "Prototype. Answers come only from our own venue data, no AI model. Ask about places to play, events, groups, how to try a sport, what is in the map view, or how RacketConnect works. Nothing is booked or paid here. Your sport and city are remembered in this browser only."));
      addChips(root.Ask.starters);
    }

    function open(on) {
      panel.hidden = !on; fab.hidden = on; fab.setAttribute("aria-expanded", on ? "true" : "false");
      if (on) { if (!log.firstChild) intro(); input.focus(); } else fab.focus();
    }
    fab.addEventListener("click", () => open(true));
    close.addEventListener("click", () => open(false));
    panel.addEventListener("keydown", e => { if (e.key === "Escape") open(false); });
    form.addEventListener("submit", e => { e.preventDefault(); go(input.value); input.value = ""; });
  }

  root.AskWidget = {mount};
})(window);
