// RacketConnect "ask box", layer 1 (docs/chatbot_plan.md, ADR 0033): free, rule-based, no AI model, no server.
// Reads a question, picks out sport / place / intent, and answers ONLY from venues.json (sport descriptions and facts come from its sports list).
// Works in the browser (window.Ask) and in Node (module.exports) so chatbot/test_ask.js can check the 30 questions.
(function (root) {
  "use strict";
  const norm = s => " " + String(s || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim() + " ";
  const has = (t, re) => re.test(t);
  const SURF = {1: "indoor", 2: "outdoor", 4: "sand", 8: "clay", 16: "grass", 32: "hard", 64: "turf"};
  const CONFIRM = {v: "confirmed in person", o: "stated by the operator", r: "reported, not independently confirmed"};
  const OFFER = {O: "open play", C: "clinics", L: "private lessons", G: "group classes", D: "drop-in", T: "tournaments", E: "leagues", S: "social events"};
  const SPORT_ALIASES = {"pickle ball": "Pickleball", "racket ball": "Racquetball", "ping pong": "Table Tennis", "paddle tennis": "Pop Tennis", "poptennis": "Pop Tennis"};
  // alias -> [centre city, radius km, label shown, 1 = wide area]
  const PLACE_ALIASES = {"la": ["Los Angeles", 12, "Los Angeles"], "vegas": ["Las Vegas", 12, "Las Vegas"], "sf": ["San Francisco", 12, "San Francisco"], "san fran": ["San Francisco", 12, "San Francisco"],
    "bay area": ["San Francisco", 60, "the Bay Area", 1], "silicon valley": ["San Jose", 30, "Silicon Valley", 1], "orange county": ["Santa Ana", 25, "Orange County", 1],
    "inland empire": ["Riverside", 40, "the Inland Empire", 1], "lake tahoe": ["South Lake Tahoe", 30, "Lake Tahoe", 1], "tahoe": ["South Lake Tahoe", 30, "Lake Tahoe", 1]};
  const SKIP_CITY = new Set(["industry", "commerce", "mesa", "alpine", "orange", "bell", "mount", "live oak", "acme", "hope"]);
  const GEAR = / (buy|shop|shops|store|stores|rent|rental|rentals|restring|restrung|stringing|deals|cheapest|discount) /;
  const EVENTS = / (watch|tournament|tournaments|event|events|spectate|spectators|big screen|this weekend|tonight|this week|what s on) /;
  const WALLS = / (wall|walls|backboard|backboards|hit against|hitting wall) /;
  const LEARN = / (what is|what s|whats|get started|how do i start|how do i begin|difference|different|vs|versus|same as|should i try|equipment|rules|what sport|recommend) /;
  const SOCIAL = / (play with|who can i play|people to play|someone to play|meet people|find people|partner|partners|group|groups|league|leagues|meetup|social|join a team|teams) /;
  const SOCIAL2 = / play w+ with /;
  const BOOK = / (book|reserve|reservation|reservations) /;
  const RACKET = / (court|courts|racket|rackets|racquet|racquets|paddle|paddles|shuttlecock|tennis|net) /;
  const REFUSE = "I only help with racket sports, courts, and where to buy or rent racket-sport gear. Ask me about places to play, events to watch, or how to try a sport.";

  function km(a, b, c, d) {
    const p = Math.PI / 180, h = Math.sin((c - a) * p / 2) ** 2 + Math.cos(a * p) * Math.cos(c * p) * Math.sin((d - b) * p / 2) ** 2;
    return 12742 * Math.asin(Math.sqrt(h));
  }

  function create(data, store) {
    store = store || {get: () => ({}), set: () => {}, clear: () => {}};
    const sports = data.sports;
    // sport keys (longest first so "pop tennis" beats "tennis")
    const sportKeys = [];
    sports.forEach((s, i) => { if (s.v > 0) sportKeys.push({key: norm(s.n), name: s.n, idx: i}); });
    for (const [alias, name] of Object.entries(SPORT_ALIASES)) {
      const i = sports.findIndex(s => s.n === name);
      if (i >= 0) sportKeys.push({key: norm(alias), name, idx: i});
    }
    sportKeys.sort((a, b) => b.key.length - a.key.length);
    // cities and their centres
    const cities = new Map();
    for (const v of data.venues) {
      if (!v.c) continue;
      const k = norm(v.c);
      const e = cities.get(k) || {name: v.c.replace(/\b(\w)(\w*)/g, (m, a, b) => a.toUpperCase() + b.toLowerCase()), n: 0, y: 0, x: 0};
      e.n++; e.y += v.y; e.x += v.x; cities.set(k, e);
    }
    const cityKeys = [...cities.keys()].filter(k => k.length > 5 && !SKIP_CITY.has(k.trim())).sort((a, b) => b.length - a.length);
    const placeAliasKeys = Object.keys(PLACE_ALIASES).map(a => [norm(a), a]).sort((a, b) => b[0].length - a[0].length);

    function detectSports(t) {
      let rest = t;
      const found = [];
      for (const s of sportKeys) {
        const pos = rest.indexOf(s.key);
        if (pos >= 0) {
          if (!found.some(f => f.idx === s.idx)) found.push({idx: s.idx, name: s.name, pos});
          rest = rest.slice(0, pos) + " ".repeat(s.key.length) + rest.slice(pos + s.key.length);
        }
      }
      return found.sort((a, b) => a.pos - b.pos);
    }

    function detectPlace(t) {
      for (const [k, a] of placeAliasKeys) {
        if (t.includes(k)) {
          const [city, r, label, area] = PLACE_ALIASES[a], c = cities.get(norm(city));
          if (c) return {label, area: !!area, y: c.y / c.n, x: c.x / c.n, r, city: norm(city)};
        }
      }
      for (const k of cityKeys) {
        if (t.includes(k)) { const c = cities.get(k); return {label: c.name, y: c.y / c.n, x: c.x / c.n, r: 12, city: k}; }
      }
      return null;
    }

    const STATES = {california: "CA", nevada: "NV", oregon: "OR", washington: "WA", hawaii: "HI"};
    const stateOf = t => { for (const [n, c] of Object.entries(STATES)) if (t.includes(" " + n + " ")) return c; return t.includes(" nv ") ? "NV" : t.includes(" ca ") ? "CA" : ""; };
    // events and groups carry no state: use the state of the nearest venue pin
    const stateAt = (y, x) => { let best = "", bd = 1e9; for (const v of data.venues) { const d = (v.y - y) ** 2 + (v.x - x) ** 2; if (d < bd) { bd = d; best = v.r; } } return best; };
    const venueLink = v => (v.w && /^https?:\/\//.test(v.w)) ? v.w : (v.ac || []).map(a => a[2]).find(u => /^https?:\/\//.test(u || "")) || "";

    function venueItem(v, idx, dist, dupName) {
      const f = v.f || 0, p = v.p.find(e => e[0] === idx) || [idx, 0, 0];
      const access = (f & 8) ? "members-only (marked private/members)" : (f & 2) ? "public" : "access not stated";
      const bits = [[v.c, v.r].filter(Boolean).join(" "), access];
      if (v.xu) bits.push("public access not confirmed");
      if (f & 4) bits.push("free"); if (f & 1) bits.push("lit");
      if (p[1]) bits.push(p[1] + " court" + (p[1] > 1 ? "s" : ""));
      const surf = Object.entries(SURF).filter(([b]) => p[2] & b).map(([, l]) => l); if (surf.length) bits.push(surf.join("/"));
      const off = [...(v.o || "")].map(c => OFFER[c]).filter(Boolean); if (off.length) bits.push("offers " + off.join(", "));
      if (v.cf) bits.push(CONFIRM[v.cf] + (v.cd ? " (" + v.cd + ")" : ""));
      if (dist != null) bits.push(Math.round(dist * 10) / 10 + " km away");
      if (v.a) bits.push(v.a + (v.ai ? " (nearest address, inferred)" : v.ap ? " (park/school address, inferred)" : ""));
      else if (v.ns) bits.push("near " + v.ns + " (inferred)");
      return {title: dupName ? (v.n || "Unnamed court") + " (" + (v.a || v.c || "address not stated") + ")" : (v.n || "Unnamed court"), detail: bits.join(" · "), url: venueLink(v)};
    }

    function searchVenues(sp, loc, st, flt) {
      const rows = [];
      for (const v of data.venues) {
        if (v.kd === "w" || !v.p.some(e => e[0] === sp.idx && e[2] !== 128)) continue;
        if (st && v.r !== st) continue;
        const f = v.f || 0;
        if (flt.pub && !(f & 2)) continue;
        if (flt.free && !(f & 4)) continue;
        if (flt.lit && !(f & 1)) continue;
        let d = null;
        if (loc) { d = km(loc.y, loc.x, v.y, v.x); if (d > loc.r) continue; }
        rows.push([v, d]);
      }
      rows.sort((a, b) => ((a[0].q !== "c") - (b[0].q !== "c")) || ((a[1] || 0) - (b[1] || 0)));
      return rows;
    }

    function venuesAnswer(sp, loc, st, t, lead) {
      const want = {pub: has(t, / (public|non members|non member|nonmembers|open to the public) /) || has(t, / free /), free: has(t, / (free|no cost) /), lit: has(t, / (lit|lights|lighting|night|evening) /)};
      const where = loc ? (loc.area ? "in " : "near ") + loc.label : st ? "in " + st : "in the states we cover";
      let rows = searchVenues(sp, loc, st, want), notes = [];
      if (!rows.length && (want.pub || want.free || want.lit)) {
        const dropped = [want.free && "marked free", want.lit && "marked lit", want.pub && !want.free && "marked public"].filter(Boolean);
        notes.push("No " + sp.name + " place " + where + " is " + dropped.join(" or ") + " in our data. That often means it isn't recorded, not that it's false. Here are the places we do have:");
        rows = searchVenues(sp, loc, st, {});
      }
      if (!loc && !st && rows.length > 8) {
        return {kind: "clarify", lines: [lead, "We hold " + rows.length + " places for " + sp.name + " across the states we cover. Which city or area? (for example Reno, Las Vegas, San Diego, the Bay Area)"], items: []};
      }
      if (!rows.length) return {kind: "venues", lines: [lead, "No " + sp.name + " places found " + where + " in our data. That does not prove there are none; it may just not be mapped yet."], items: []};
      const applied = [want.free && "free", want.lit && "lit", want.pub && !want.free && "public"].filter(Boolean);
      if (applied.length && !notes.length) notes.push("Only places marked " + applied.join(" and ") + " in our data are shown.");
      const shown = rows.slice(0, 5), names = {};
      shown.forEach(([v]) => { names[v.n] = (names[v.n] || 0) + 1; });
      return {kind: "venues", lines: [lead, ...notes, "Found " + rows.length + " " + sp.name + " place" + (rows.length > 1 ? "s" : "") + " " + where + " (showing " + shown.length + "). Cost, courts and access are only shown when our data has them."],
        items: shown.map(([v, d]) => venueItem(v, sp.idx, d, names[v.n] > 1))};
    }

    function eventsAnswer(sp, loc, st, t) {
      const today = new Date().toISOString().slice(0, 10), weekEnd = new Date(Date.now() + 7 * 864e5).toISOString().slice(0, 10);
      const soon = has(t, / (this weekend|tonight|this week|today) /);
      let ev = data.events.filter(e => (e.e || e.s || "9999") >= today && (!sp || e.sp === sp.name) && (!st || stateAt(e.y, e.x) === st)
        && (!loc || norm(e.c) === " " + loc.city.trim() + " " || km(loc.y, loc.x, e.y, e.x) <= Math.max(loc.r, 25)) && (!soon || (e.s || "") <= weekEnd));
      ev.sort((a, b) => (a.s || "").localeCompare(b.s || ""));
      const lines = [];
      if (has(t, / big screen /)) lines.push("We list events you can attend in person. Screenings of matches on a big screen aren't covered yet.");
      if (!ev.length) lines.push("No upcoming" + (sp ? " " + sp.name : "") + " events listed" + (loc ? (loc.area ? " in " : " near ") + loc.label : st ? " in " + st : "") + (soon ? " this week" : "") + " in our data (as of " + data.meta.generated + ").");
      else lines.push(ev.length + " upcoming event" + (ev.length > 1 ? "s" : "") + " in our data:");
      return {kind: "events", lines, items: ev.slice(0, 5).map(e => ({title: e.n, detail: [e.s + (e.e && e.e !== e.s ? " to " + e.e : ""), e.v + ", " + e.c, e.sp, e.d === "confirmed" ? "dates confirmed" : "dates " + e.d, e.t].filter(Boolean).join(" · "), url: /^https:\/\//.test(e.u || "") ? e.u : ""}))};
    }

    function wallsAnswer(sp, loc, st) {
      const acc = a => ["public", "yes", "permissive"].includes(a) ? "public" : ["restricted", "private", "customers", "members", "no"].includes(a) ? "restricted" : "access not checked";
      const near = v => !loc || km(loc.y, loc.x, v.y, v.x) <= Math.max(loc.r, 15);
      const w = data.venues.filter(v => v.kd === "w" && (!st || v.r === st) && near(v)
        && (!sp || v.p.some(e => e[0] === sp.idx) || (v.hw.sp || []).some(s => norm(s).includes(norm(sp.name)))));
      w.sort((a, b) => loc ? km(loc.y, loc.x, a.y, a.x) - km(loc.y, loc.x, b.y, b.x) : 0);
      const onSite = data.venues.filter(v => v.wl && v.kd !== "w" && (!st || v.r === st) && near(v)).length;
      const where = loc ? (loc.area ? " in " : " near ") + loc.label : st ? " in " + st : "";
      if (!w.length) return {kind: "walls", lines: ["No stand-alone hitting walls found" + where + " in our data. That does not prove there are none." + (onSite ? " " + onSite + " court venues there have walls on site." : "")], items: []};
      return {kind: "walls", lines: ["Found " + w.length + " stand-alone hitting wall pin" + (w.length > 1 ? "s" : "") + where + " (showing " + Math.min(5, w.length) + "). Many are only tagged in OpenStreetMap, not verified." + (onSite ? " Another " + onSite + " court venues have walls on site." : "")],
        items: w.slice(0, 5).map(v => ({title: (v.n || "Hitting wall") + (v.c ? " (" + v.c + ")" : ""),
          detail: [(v.hw.t || []).join(", "), v.hw.wn > 1 ? v.hw.wn + " walls" : "", acc(v.hw.ac), v.hw.cf === "tagged" ? "from OpenStreetMap tags, not checked" : v.hw.cf, v.hw.l === 1 ? "lit" : "", v.hw.f === 1 ? "free" : "", v.y.toFixed(4) + ", " + v.x.toFixed(4)].filter(Boolean).join(" · "), url: ""}))};
    }

    function socialAnswer(sp, loc, st) {
      const near = o => !loc || km(loc.y, loc.x, o.y, o.x) <= Math.max(loc.r, 25);
      const groups = (data.social || []).filter(g => (!sp || g.sp === sp.name) && near(g) && (!st || stateAt(g.y, g.x) === st));
      const apps = (data.platforms || []).filter(p => !sp || (p.sp || []).includes(sp.idx));
      const where = loc ? (loc.area ? " in " : " near ") + loc.label : st ? " in " + st : "";
      const lines = [groups.length ? groups.length + " recurring group" + (groups.length > 1 ? "s" : "") + " listed" + where + (sp ? " for " + sp.name : "") + " (each links to the organizer):" : "No recurring groups or leagues listed" + where + (sp ? " for " + sp.name : "") + " in our data."];
      const https = u => /^https:\/\//.test(u || "") ? u : "";
      const items = groups.slice(0, 4).map(g => ({title: g.n, detail: [g.o, g.v + ", " + g.c, g.sc, g.sl && "level: " + g.sl, g.pi].filter(Boolean).join(" · "), url: https(g.g) || https(g.u)}));
      if (apps.length) { lines.push("Player-matching apps (we link out; we haven't tested them):"); apps.slice(0, 3).forEach(p => items.push({title: p.n, detail: p.d + " · listed " + p.vo, url: https(p.u)})); }
      return {kind: "social", lines, items};
    }

    const sportByName = n => sports.find(s => s.n === n);
    function describe(s) {
      const f = s.f || {}, bits = [f.c && "court " + f.c + " ft", f.p && f.p + " players", f.g && "gear: " + f.g, f.o && "governing body " + f.o].filter(Boolean);
      return s.n + ": " + (s.d || "no description yet.") + (bits.length ? " (" + bits.join("; ") + ")" : "");
    }
    const linkItem = s => (s.u && /^https:\/\//.test(s.u.l || "")) ? [{title: "Learn more about " + s.n, detail: "", url: s.u.l}] : [];

    function learnAnswer(found, t) {
      const named = found.map(f => sportByName(f.name)).filter(Boolean);
      if (has(t, / pop tennis /) && has(t, / paddle tennis /) && sportByName("Pop Tennis")) return {kind: "learn", lines: ["In our sport list pop tennis and paddle tennis are the same sport: " + describe(sportByName("Pop Tennis"))], items: linkItem(sportByName("Pop Tennis"))};
      if (has(t, / (should i try|recommend|what sport) /)) {
        const picks = ["Pickleball", "Pop Tennis", "Padel", "Table Tennis"].map(sportByName).filter(Boolean);
        return {kind: "learn", lines: ["General suggestions if you like tennis and want something gentler: sports on smaller courts with slower balls and doubles play are usually easier to start. Check with a doctor if you have an injury.", ...picks.map(describe)], items: []};
      }
      if (named.length >= 2) return {kind: "learn", lines: ["From our sport list:", ...named.slice(0, 2).map(describe)], items: named.slice(0, 2).flatMap(linkItem)};
      if (named.length === 1) {
        const s = named[0], eq = has(t, / equipment /);
        const lines = eq ? [(s.f && s.f.g ? "Gear listed for " + s.n + ": " + s.f.g + "." : "No gear is listed for " + s.n + " yet.") + " That is the type of equipment only; I have no store or price data yet."] : ["From our sport list: " + describe(s)];
        return {kind: "learn", lines: [...lines, "Tell me a city and I'll look for places to play " + s.n + "."], items: linkItem(s)};
      }
      return {kind: "clarify", lines: ["Which sport do you mean? I can describe any sport on our list, for example tennis, pickleball, padel, pop tennis, squash, racquetball, badminton, table tennis or beach tennis."], items: []};
    }

    function answer(question) {
      const t = norm(question);
      const profile = store.get() || {};
      let found = detectSports(t), loc = detectPlace(t), st = stateOf(t);
      const lines0 = [];
      if (has(t, / (forget|clear) (me|my profile|what i said|everything) /)) { store.clear(); return {kind: "profile", lines: ["Cleared. Nothing is saved in this browser now."], items: []}; }
      if (has(t, / (what did i say|what do i play|my profile|what do you remember|what do you know about me) /)) {
        return {kind: "profile", lines: Object.keys(profile).length ? ["Saved in this browser only: " + Object.entries(profile).map(([k, v]) => k + " = " + v).join(", ") + ". Say \"forget me\" to clear it."] : ["I don't have anything saved yet. Tell me, for example, \"I play padel in Reno, beginner\"."], items: []};
      }
      if (/^ (i play|i m into|i am into|i like|i love|im a|i m a|i am a|my level is|i live in) /.test(t) && (found.length || loc)) {
        const lvl = (t.match(/ (beginner|intermediate|advanced) /) || [])[1];
        const next = Object.assign({}, profile, found[0] ? {sport: found[0].name} : {}, loc ? {city: loc.label} : {}, lvl ? {level: lvl} : {});
        store.set(next);
        lines0.push("Got it: " + Object.entries(next).map(([k, v]) => k + " " + v).join(", ") + " (saved in this browser only; say \"forget me\" to clear).");
      }
      if (!found.length && !has(t, / (learn|equipment|rules) /) && profile.sport && has(t, / (where|play|courts|near|closest|should i) /) && !has(t, GEAR) && !has(t, WALLS) && !has(t, EVENTS)) {
        const i = sports.findIndex(s => s.n === profile.sport); if (i >= 0) found = [{idx: i, name: profile.sport, pos: 0}]; lines0.push("Using your saved sport: " + profile.sport + ".");
      }
      if (!loc && !st && profile.city && has(t, / (where|near|closest|should i|play) /) && found.length && !has(t, EVENTS)) { loc = detectPlace(norm(profile.city)); if (loc) lines0.push("Using your saved city: " + profile.city + "."); }
      const lead = lines0.join(" ");
      const sp = found[0] || null;
      const done = r => { if (lead && !r.lines.includes(lead)) r.lines.unshift(lead); return r; };

      if (has(t, BOOK) || (has(t, / rent /) && has(t, / (court|courts) /))) {
        const r = {kind: "booking", lines: ["I can't book or take payments; RacketConnect only links out. Use the venue's own booking page" + (sp && loc ? " (links shown on each place below when we have them)." : ". Tell me a sport and city and I'll show places with their links.")], items: []};
        if (sp && loc) { const v = venuesAnswer(sp, loc, st, t, ""); r.items = v.items; }
        return done(r);
      }
      if (has(t, GEAR) && !has(t, / equipment /)) {
        return done({kind: "gear", lines: ["I don't have racket-shop, restringing or rental data yet, so I won't name stores. " + (sp ? "I can show places to play " + sp.name + (loc ? (loc.area ? " in " : " near ") + loc.label : "") + " instead; some offer clinics or lessons where you can try gear. " : "") + "A ranked gear list (sport specialists first, then general sporting goods, then big-box) is planned once the data exists."], items: []});
      }
      if (has(t, EVENTS)) return done(eventsAnswer(sp, loc, st, t));
      if (has(t, WALLS)) return done(wallsAnswer(sp, loc, st));
      if (has(t, SOCIAL) || has(t, SOCIAL2)) return done(socialAnswer(sp, loc, st));
      if (has(t, / paddle | paddles /) && !found.length && !has(t, / (padel|pop tennis|pickleball|beach tennis) /)) return done({kind: "clarify", lines: ["\"Paddle\" can mean a pickleball paddle, pop tennis (also called paddle tennis), or padel (a different sport on a walled court). Which one?"], items: []});
      if (has(t, LEARN) || (found.length && has(t, / (how do i|beginner|get started) /))) return done(learnAnswer(found, t));
      if (sp) return done(venuesAnswer(sp, loc, st, t, ""));
      if (loc && has(t, RACKET)) return done({kind: "clarify", lines: ["Which sport " + (loc.area ? "in " : "near ") + loc.label + "? For example tennis, pickleball, padel, squash or racquetball."], items: []});
      if (has(t, RACKET)) return done({kind: "clarify", lines: ["Tell me the sport and a city, for example \"pickleball in Reno\"."], items: []});
      return {kind: "refuse", lines: [REFUSE], items: []};
    }
    return {answer};
  }

  const api = {create};
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.Ask = api;
})(typeof window !== "undefined" ? window : globalThis);
