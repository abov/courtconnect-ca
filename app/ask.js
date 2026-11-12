// RacketConnect "ask box", layer 1 (docs/chatbot.md, ADR 0033): free, rule-based, no AI model, no server.
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
  const SKIP_CITY = new Set(["industry", "commerce", "mesa", "alpine", "orange", "bell", "mount", "live oak", "acme", "hope", "wall"]);
  const GEAR = / (buy|shop|shops|store|stores|rent|rental|rentals|restring|restrung|stringing|deals|cheapest|discount) /;
  const EVENTS = / (watch|tournament|tournaments|event|events|spectate|spectators|big screen|this weekend|tonight|this week|what s on) /;
  const WALLS = / (wall|walls|backboard|backboards|hit against|hitting wall) /;
  const LEARN = / (what is|what s|whats|get started|how do i start|how do i begin|difference|different|vs|versus|same as|should i try|equipment|rules|what sport|recommend) /;
  const SOCIAL = / (play with|who can i play|people to play|someone to play|meet people|find people|partner|partners|group|groups|league|leagues|meetup|social|join a team|teams) /;
  const SOCIAL2 = / play w+ with /;
  const BOOK = / (book|reserve|reservation|reservations) /;
  const COUNT = / (how many|number of|count of|counts|totals?|tally|by state|by country|per state|per country|each state) |^ count /;
  // issue 617: "when will X open?" and "when will you add Y?" get what we know plus a way to ask, never a guessed date
  const WHEN_OPEN = / when (will|does|is|are|do|should|would) (.* )?(open|opens|opening|reopen|reopens|reopening|ready|launch|launching|built|finished|done) | opening (date|day) | (grand )?opening soon | coming soon | open yet /;
  const WHEN_ADD = / when (will|are|do|would|is) (you|racketconnect|it|the (app|map|site)) (.* )?(add|adding|cover|covering|expand|expanding|include|including|support|get|have) /;
  const RACKET = / (court|courts|racket|rackets|racquet|racquets|paddle|paddles|shuttlecock|tennis|net) /;
  // Replies that are not an answer (hello, thanks, off-topic, ...) stay kind and always offer a next step as chips (todo: docs/chatbot.md).
  const STARTERS = ["Pickleball in Reno", "Padel in Las Vegas", "Squash in the Bay Area", "What is pop tennis?", "What is RacketConnect?"];
  // Questions about the page the visitor is looking at (needs the map's context from the widget; without it they fall through to the normal routing).
  const VIEW = / (this view|in view|on screen|on the screen|on the map|am i looking at|i m looking at|you re looking at|this pin|this court|this place|this venue|this spot|this one|selected|around here|nearby|near me|close to me|closest to me|visible) /;
  const VIEW_THIS = / (am i looking at|i m looking at|this pin|this court|this place|this venue|this spot|this one|selected|open) /;
  const PRODUCT_URL = {change: "https://github.com/abov/courtconnect-ca/issues/new?template=suggest-a-change.yml", event: "https://github.com/abov/courtconnect-ca/issues/new?template=report-an-event.yml", code: "https://github.com/abov/courtconnect-ca", ask: "https://github.com/abov/courtconnect-ca/issues/new"};
  const PRODUCT_CHIPS = ["What does confirmed mean?", "How do I add my club?", "Where does your data come from?", "Which states do you cover?"];
  // About RacketConnect itself. Every line repeats what the About card, README and llms.txt already say; nothing here is new policy.
  // [pattern, lines, link items, chips]
  const PRODUCT = [
    [/ (add|submit|claim) (my|our|this) (club|clubs|venue|court|courts|listing|facility|gym|place|business|event|tournament|league) | (add|submit) (a|an) (club|venue|listing|facility|event|tournament|league) | (is|are) (missing|wrong|incorrect|outdated) | (missing|wrong|incorrect|outdated) (club|venue|court|listing|place|address|info|hours) | report (a|an) (mistake|error|problem|closure) | suggest a change | (fix|update|correct) (my|our|this|the) (listing|address|info|hours) /,
      ["Is a place missing or wrong? Send us a link to its public page; a reviewer checks it and updates the listing when the page backs it up. No sign-in is needed. A listing changes only with public evidence; it can't be bought."],
      [{title: "Suggest a change or add a place", detail: "GitHub form", url: PRODUCT_URL.change}, {title: "Add an event, league or open play", detail: "GitHub form", url: PRODUCT_URL.event}], ["What does confirmed mean?", "Which states do you cover?"]],
    [/ (what does|what do|what s|whats|meaning of|mean by|explain) (.* )?(confirmed|reported|official|inferred|labels?|badges?|checked) | how (sure|certain) (.* )?(are you|is this)| (confirmed|inferred) (mean|means) /,
      ["Each place says how sure we are. Confirmed: someone checked it in person. Official: the operator's own public page says so. Reported: a person told us and we haven't independently confirmed it. No label means the pin comes from map data only (OpenStreetMap or Overture), so treat access, hours and prices as unknown until you check the venue's own page. Street addresses marked inferred are the nearest address or road, not confirmed."],
      [], ["Where does your data come from?", "How up to date is this?"]],
    [/ (where|how) (.* )?(data|info|information|listings?|venues?) (.* )?(come from|comes from|sourced|collected) | where (do|does) (you|racketconnect|this) get | data sources? | your sources? | (openstreetmap|osm|overture) | how (do|did) you (know|collect|build) /,
      ["The venues come from OpenStreetMap contributors and the Overture Maps Foundation, plus places we add by hand from public pages and community reports. Events, groups and links come from the organizers' own public pages. We don't use logged-in pages, booking apps' private data or Google Places. The pipeline is open source."],
      [{title: "How it's built", detail: "numbers and limits", url: "how-its-built.html"}], ["What does confirmed mean?", "How up to date is this?"]],
    [/ (how|is it|is this|are you|are the) (.* )?(accurate|up to date|current|fresh|reliable|trust|trustworthy) | how (often|frequently) (.* )?(updated|refreshed|update|refresh) | (last|latest) (updated|refresh|refreshed) | out of date | outdated /,
      ["The data is rebuilt about twice a month. Public access, hours and prices are often unknown, so I only say them when our data has them, and each place shows when it was last checked. If something is wrong, tell us and a reviewer will check it."],
      [{title: "Suggest a change", detail: "GitHub form", url: PRODUCT_URL.change}], ["What does confirmed mean?", "How do I add my club?"]],
    [/ (which|what) (states|regions|countries) | (do you|does it|does racketconnect|will you|are you going to) (cover|support|expand|add) | (mexico|canada|europe|texas|florida|new york|colorado|utah|idaho|montana|new mexico) | outside (of )?(california|the us|the u s|these states) /,
      ["We cover California, Nevada, Oregon, Washington, Arizona, Texas and Hawaii, plus a Mexico pilot: the border cities (Tijuana, Mexicali, Ensenada, Hermosillo, Nogales, San Luis Río Colorado) have automatic map data, and Mexico City, Guadalajara, Monterrey, Cancún, Playa del Carmen and Mérida have clubs added by hand from their own public pages. Coverage in Mexico is partial, and other places aren't on the map yet."],
      [], ["Pickleball in Reno", "Padel in Las Vegas", "Tennis in Seattle"]],
    [/ (is|are) (this|it|racketconnect|the (app|site|map|website)) (really |completely |a )?free | free to use | (do|will) i (need|have to) (.* )?(account|sign up|sign in|log in|login|pay|register) | (an |any )?account | sign up | sign in | log in | login | subscription | cost to use | how much (does|is) (racketconnect|the (app|site|map)|this (app|site|map)) /,
      ["RacketConnect is free to use. There are no accounts, no sign-in and no paid or featured placement. We link out to each venue's own page; we never take bookings or payments."],
      [], ["Pickleball in Reno", "What is pop tennis?"]],
    [/ (privacy|tracking|tracked|cookies|cookie|personal (data|information)|my data|do you (store|save|collect|sell)) /,
      ["There are no accounts. We count anonymous page visits and which kinds of places get opened (a count of looks, nothing about who you are). Your questions are not saved; the only text we receive is a question you press \"Send this question to us\" on, with emails, links and phone-like numbers removed. If you tell this box your sport and city, they are remembered in your browser only; say \"forget me\" to clear them."],
      [], ["Forget me", "What did I say I play?"]],
    [/ (who|what company|which company) (made|built|created|runs|owns|is behind|developed) | (contact|email|e mail|reach) (you|the team|someone|support|the owner)| support team | is (this|it) (open source|a startup|a company) | open source /,
      ["RacketConnect is an independent, open-source project. The code and the data pipeline are public, and the issue forms are the way to reach us: they go to a reviewer, no sign-in needed."],
      [{title: "Source code and docs", detail: "GitHub", url: PRODUCT_URL.code}, {title: "Suggest a change", detail: "GitHub form", url: PRODUCT_URL.change}], undefined],
    [/ (spanish|espanol|español|portuguese|french|german|translate|translation|translated|other languages?|in english) | (language|languages) /,
      ["RacketConnect is written in English and has no translation of its own. Your browser can translate the page: Chrome and Edge have a Translate button in the address bar, Safari has it in the aA menu. Place, event and group names stay as written, and machine translation can be wrong."],
      [], undefined],
    [/ (app store|play store|google play|iphone app|android app|ios app|mobile app|an app|download|install) /,
      ["There is no app to download. RacketConnect is a website that works in your phone's browser, so you can open it and add it to your home screen if you like."],
      [], undefined],
    [/ (what is|what s|whats|what are|tell me about|explain|describe) (racketconnect|racket connect|this (site|app|map|website|tool|project|bot|chat|chatbot))( | for )| (what|how) (do|does) (racketconnect|this (site|app|map|website|tool)|you) (do|work|help) | what can i (do|use) (here|this|it) for | racketconnect is | (about|purpose of) (racketconnect|this (site|app|map|website)) /,
      ["RacketConnect is one free map of racket-sport venues in California, Nevada, Oregon, Washington, Arizona, Texas, Hawaii and parts of Mexico: tennis, pickleball, padel, squash, badminton, table tennis and the lesser-known sports. Use it to find a court, see events to watch, find groups to play with, and learn how to try a sport. Each place says how sure we are, and we link out to the venue's own page; we never take bookings or payments.", "This box is a simple helper with no AI model. It answers only from our own venue data."],
      [], PRODUCT_CHIPS],
    [/ (how (do|can|would) i (use|search|filter|find|get around)|how to use|how does (the |this )?(map|site|app) work|what do (the )?(pins|markers|dots|colors|colours|icons|circles) mean|legend|orange pins|grey pins|gray pins) /,
      ["Pick a sport and zoom to your area, or type a city, ZIP or venue name in the search box; the list follows what the map shows. Tap a pin for its details, how sure we are, and the link to the venue's own page. Orange pins are stand-alone hitting walls. You can also switch between places to play, events to watch and groups."],
      [], ["What does confirmed mean?", "What's in this view?"]]
  ];
  const POPULAR = ["Los Angeles", "San Diego", "the Bay Area", "Las Vegas", "Seattle"];
  const SPORT_CHIPS = ["Tennis", "Pickleball", "Padel", "Squash"];
  const GREETING = /^ (hi|hello|hey|hiya|howdy|yo|hola|sup|good morning|good afternoon|good evening)( there| again| everyone| all| bot)? $/;
  const HELP = /^ (help|help me|i need help|can you help|can you help me|menu|start) $| (what can you do|what do you do|who are you|how does this work|how do you work|what can i ask) /;
  const THANKS = / (thanks|thank you|thx|cheers|appreciate it) /;
  const FRUSTRATED = / (useless|not helpful|unhelpful|doesn t work|does not work|not working|stupid|dumb|bad bot|this sucks|terrible|that s wrong|that is wrong|not what i asked|not what i wanted|you re wrong) /;
  const OTHER_SPORT = / (golf|cricket|soccer|football|basketball|baseball|softball|hockey|volleyball|swimming|swim|running|jogging|yoga|pilates|rugby|skiing|snowboarding|skateboarding|bowling|boxing|lacrosse|cycling|climbing|surfing|hiking|fishing|archery|darts|billiards|chess) /;
  const sportChips = (loc, skip) => SPORT_CHIPS.filter(n => n !== skip).slice(0, 4).map(n => n + " in " + loc.label);
  const cityChips = sp => POPULAR.map(c => sp.name + " in " + c);

  // Replies that did not answer: a refusal, a frustrated visitor, no gear data, or a search with no results. The widget offers "send this question to us" on these.
  const MISS_KINDS = new Set(["refuse", "support", "gear"]);
  const RESULT_KINDS = new Set(["venues", "events", "social", "walls"]);
  // A question the visitor chooses to send: emails, links and phone-like numbers are cut out first, whitespace collapsed, 200 characters at most.
  // ingestion/extract_ask_feedback.py runs the same rules again before anything reaches the warehouse.
  function scrub(text) {
    return String(text || "").replace(/[^\s@]+@[^\s@]+/g, "[email]").replace(/(https?:\/\/|www\.)\S+/gi, "[link]")
      .replace(/\+?\d[\d\s().-]{6,}\d/g, "[number]").replace(/\s+/g, " ").trim().slice(0, 200);
  }

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
    // One entry per city NAME, counted per state first: Reno, San Diego and Henderson also exist in Texas, and averaging both
    // places would put the centre in the wrong spot. The state with the most pins for a name wins.
    const cities = new Map(), byState = new Map();
    for (const v of data.venues) {
      if (!v.c) continue;
      const k = norm(v.c), ks = k + "|" + (v.r || "");
      const e = byState.get(ks) || {k, name: v.c.replace(/\b(\w)(\w*)/g, (m, a, b) => a.toUpperCase() + b.toLowerCase()), n: 0, y: 0, x: 0};
      e.n++; e.y += v.y; e.x += v.x; byState.set(ks, e);
    }
    for (const e of byState.values()) { const cur = cities.get(e.k); if (!cur || e.n > cur.n) cities.set(e.k, e); }
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

    const STATES = {california: "CA", nevada: "NV", oregon: "OR", washington: "WA", hawaii: "HI", arizona: "AZ", texas: "TX"};
    const stateOf = t => { for (const [n, c] of Object.entries(STATES)) if (t.includes(" " + n + " ")) return c; return t.includes(" nv ") ? "NV" : t.includes(" ca ") ? "CA" : t.includes(" az ") ? "AZ" : ""; };
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

    const ASK_ITEM = {title: "Ask us on GitHub", detail: "needs a free GitHub account; you get a notification when we reply", url: PRODUCT_URL.ask};
    function whenOpen(sp, loc, st, t) {
      // a place named in the question wins; otherwise filter by sport and area (a wider radius: city centres are rough)
      const all = data.venues.filter(v => v.up), named = all.filter(v => v.n && t.includes(" " + norm(v.n.replace(/\(.*\)/, "")).trim() + " "));
      const soon = named.length ? named : all.filter(v => (!sp || v.p.some(e => e[0] === sp.idx)) && (!st || v.r === st) && (!loc || km(loc.y, loc.x, v.y, v.x) <= Math.max(loc.r, 30)));
      const where = named.length ? "" : loc ? (loc.area ? " in " : " near ") + loc.label : st ? " in " + st : "";
      const what = (sp && !named.length ? sp.name + " " : "") + (soon.length === 1 ? "place" : "places");
      const wait = "I don't predict opening dates: our data only has what each club's own page said when we checked it, and none gives a firm date. The club's site or social page is the place to watch.";
      if (!soon.length) return {kind: "opening", lines: ["No " + what + where + " are marked opening soon in our data.", wait, "If you know of one, or want us to look into a place, ask below and you'll get a notification when we reply."], items: [ASK_ITEM], chips: sp ? [sp.name + (loc ? " in " + loc.label : " in Los Angeles")] : undefined};
      const items = soon.slice(0, 5).map(v => ({title: v.n || "Unnamed place", detail: [[v.c, v.r].filter(Boolean).join(" "), v.up + (v.ud ? " (page checked " + v.ud + ")" : "")].join(" · "), url: venueLink(v)}));
      return {kind: "opening", lines: [(named.length === 1 ? (named[0].n + " is") : soon.length + " " + what + where + " " + (soon.length > 1 ? "are" : "is")) + " marked opening soon in our data" + (soon.length > 5 ? " (showing 5)" : "") + ".", wait, "Want us to check one again? Ask below and you'll get a notification when we reply."], items: [...items, ASK_ITEM]};
    }
    function whenAdd(sp, loc) {
      const lines = ["There's no date for new areas or sports yet: we add them when we can map them properly, and we'd rather say no date than guess one."];
      lines.push(loc ? "We already cover " + loc.label + "; ask for a sport and I'll look." : "Today we cover California, Nevada, Oregon, Washington, Arizona, Texas and Hawaii, plus a Mexico pilot.");
      lines.push("Tell us where you'd like us next below; requests help us decide, and you'll get a notification when we reply.");
      return {kind: "opening", lines, items: [ASK_ITEM], chips: loc ? sportChips(loc) : ["Which states do you cover?"]};
    }

    const STATE_NAMES = {CA: "California", NV: "Nevada", OR: "Oregon", WA: "Washington", AZ: "Arizona", TX: "Texas", HI: "Hawaii", MX: "Mexico"};
    function countAnswer(sp, st, t, loc) {
      const by = {}; let walls = 0;
      for (const v of data.venues) {
        if (loc && km(loc.y, loc.x, v.y, v.x) > loc.r) continue;
        if (v.kd === "w") { if (!sp && (!st || v.r === st)) walls++; continue; }
        if (sp && !v.p.some(e => e[0] === sp.idx && e[2] !== 128)) continue;
        by[v.r] = (by[v.r] || 0) + 1;
      }
      const what = (sp ? sp.name + " " : "") + "places";
      const fmt = n => n.toLocaleString("en-US");
      const chips = sp ? [sp.name + " in " + (st && st !== "MX" ? STATE_NAMES[st] : "Los Angeles"), "Which states do you cover?"] : ["Pickleball places by state", "Padel places by state", "Which states do you cover?"];
      const note = "These count places (parks, clubs, rec centers), not individual courts; court counts are only known for some places.";
      if (loc) {
        const n = Object.values(by).reduce((a, b) => a + b, 0), where = (loc.area ? "in " : "near ") + loc.label;
        return {kind: "count", lines: [fmt(n) + " " + what + " " + where + " in our data." + (walls ? " Plus " + fmt(walls) + " stand-alone hitting walls." : ""), note], items: [], chips: sp ? [sp.name + " in " + loc.label] : sportChips(loc)};
      }
      if (st && !has(t, / by (state|country) | per (state|country) | breakdown | each state /)) {
        const n = by[st] || 0;
        return {kind: "count", lines: [fmt(n) + " " + what + " in " + STATE_NAMES[st] + " in our data." + (walls ? " Plus " + fmt(walls) + " stand-alone hitting walls." : ""), note], items: [], chips};
      }
      const order = Object.keys(STATE_NAMES).filter(k => by[k]).sort((a, b) => by[b] - by[a]);
      const mx = by.MX || 0, total = order.reduce((a, k) => a + by[k], 0), us = total - mx;
      const lines = [fmt(total) + " " + what + " in our data: " + fmt(us) + " in the US and " + fmt(mx) + " in Mexico.",
        "By state: " + order.map(k => STATE_NAMES[k] + " " + fmt(by[k])).join(", ") + ".", note];
      if (!sp && walls) lines.splice(2, 0, "Plus " + fmt(walls) + " stand-alone hitting walls.");
      return {kind: "count", lines, items: [], chips};
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
        return {kind: "clarify", lines: [lead, "We hold " + rows.length + " places for " + sp.name + " across the states we cover. Which city or area? (for example Reno, Las Vegas, San Diego, the Bay Area)"], items: [], chips: cityChips(sp)};
      }
      if (!rows.length) return {kind: "venues", lines: [lead, "No " + sp.name + " places found " + where + " in our data. That does not prove there are none; it may just not be mapped yet.", loc ? "You could try another sport " + (loc.area ? "in " : "near ") + loc.label + ", or the same sport in a bigger nearby city." : "You could try a city or another sport."], items: [], chips: loc ? sportChips(loc, sp.name) : cityChips(sp)};
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
      if (!ev.length) lines.push("That doesn't mean nothing is happening, only that we haven't listed it." + (loc && sp ? " I can show places to play " + sp.name + " " + (loc.area ? "in " : "near ") + loc.label + " instead." : ""));
      return {kind: "events", lines, chips: !ev.length ? (loc && sp ? [sp.name + " in " + loc.label] : loc ? sportChips(loc) : undefined) : undefined, items: ev.slice(0, 5).map(e => ({title: e.n, detail: [e.s + (e.e && e.e !== e.s ? " to " + e.e : ""), e.v + ", " + e.c, e.sp, e.d === "confirmed" ? "dates confirmed" : "dates " + e.d, e.t].filter(Boolean).join(" · "), url: /^https:\/\//.test(e.u || "") ? e.u : ""}))};
    }

    const wallAccess = a => ["public", "yes", "permissive"].includes(a) ? "public" : ["restricted", "private", "customers", "members", "no"].includes(a) ? "restricted" : "access not checked";
    const wallItem = v => ({title: (v.n || "Hitting wall") + (v.c ? " (" + v.c + ")" : ""),
      detail: [(v.hw.t || []).join(", "), v.hw.wn > 1 ? v.hw.wn + " walls" : "", wallAccess(v.hw.ac), v.hw.cf === "tagged" ? "from OpenStreetMap tags, not checked" : v.hw.cf, v.hw.l === 1 ? "lit" : "", v.hw.f === 1 ? "free" : "", v.y.toFixed(4) + ", " + v.x.toFixed(4)].filter(Boolean).join(" · "), url: ""});
    function wallsAnswer(sp, loc, st) {
      const near = v => !loc || km(loc.y, loc.x, v.y, v.x) <= Math.max(loc.r, 15);
      const w = data.venues.filter(v => v.kd === "w" && (!st || v.r === st) && near(v)
        && (!sp || v.p.some(e => e[0] === sp.idx) || (v.hw.sp || []).some(s => norm(s).includes(norm(sp.name)))));
      w.sort((a, b) => loc ? km(loc.y, loc.x, a.y, a.x) - km(loc.y, loc.x, b.y, b.x) : 0);
      const onSite = data.venues.filter(v => v.wl && v.kd !== "w" && (!st || v.r === st) && near(v)).length;
      const where = loc ? (loc.area ? " in " : " near ") + loc.label : st ? " in " + st : "";
      if (!w.length) return {kind: "walls", lines: ["No stand-alone hitting walls found" + where + " in our data. That does not prove there are none." + (onSite ? " " + onSite + " court venues there have walls on site." : "")], items: [], chips: loc ? sportChips(loc) : undefined};
      return {kind: "walls", lines: ["Found " + w.length + " stand-alone hitting wall pin" + (w.length > 1 ? "s" : "") + where + " (showing " + Math.min(5, w.length) + "). Many are only tagged in OpenStreetMap, not verified." + (onSite ? " Another " + onSite + " court venues have walls on site." : "")],
        items: w.slice(0, 5).map(wallItem)};
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
      if (!groups.length) lines.push("That only means we haven't listed any yet" + (loc && sp ? "; I can show places to play " + sp.name + " " + (loc.area ? "in " : "near ") + loc.label + " where you might meet people." : "."));
      return {kind: "social", lines, items, chips: !groups.length && loc && sp ? [sp.name + " in " + loc.label] : undefined};
    }

    // "What am I looking at?": the open pin, or what the map shows right now. ctx() comes from the page (map bounds + current filters); absent in Node tests.
    function viewAnswer(sp, t, ctx) {
      const c = ctx(), item = (v, i) => v.kd === "w" ? wallItem(v) : venueItem(v, sp ? sp.idx : ((v.p[0] || [])[0]), null, i);
      if (c.selected && has(t, VIEW_THIS)) return {kind: "view", lines: ["You have this place open. What we know about it:"], items: [item(c.selected)], chips: ["What does confirmed mean?", "What's in this view?"]};
      let rows = c.inView || [];
      if (sp) rows = rows.filter(v => v.kd === "w" ? (v.p.some(e => e[0] === sp.idx) || (v.hw.sp || []).some(x => norm(x).includes(norm(sp.name)))) : v.p.some(e => e[0] === sp.idx && e[2] !== 128));
      const filt = (c.sport ? " The map's sport filter (" + c.sport + ") also applies." : "");
      if (!rows.length) return {kind: "view", lines: ["No" + (sp ? " " + sp.name : "") + " places in this view in our data." + filt + " Try zooming out or moving the map, or ask for a sport and city."], items: [], chips: STARTERS.slice(0, 3)};
      const names = {}; rows.slice(0, 5).forEach(v => { names[v.n] = (names[v.n] || 0) + 1; });
      return {kind: "view", lines: [rows.length + (sp ? " " + sp.name : "") + " place" + (rows.length > 1 ? "s" : "") + " in this view, nearest the centre first (showing " + Math.min(5, rows.length) + ")." + filt + (rows.length > 60 ? " Zoom in for a shorter list." : "") + " Tap a pin on the map, then ask \"what is this place?\" for its details."], items: rows.slice(0, 5).map(v => item(v, names[v.n] > 1))};
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
        return {kind: "learn", lines: [...lines, "Tell me a city and I'll look for places to play " + s.n + "."], items: linkItem(s), chips: cityChips({name: s.n})};
      }
      return {kind: "clarify", lines: ["Which sport do you mean? I can describe any sport on our list, for example tennis, pickleball, padel, pop tennis, squash, racquetball, badminton, table tennis or beach tennis."], items: [], chips: ["What is padel?", "What is pickleball?", "What is pop tennis?", "What is squash?", "What is badminton?"]};
    }

    // every reply that is not a list of results gets next-step chips
    function answer(question, ctx) {
      const r = route(question, ctx);
      if (!r.chips && !(r.items || []).length) r.chips = STARTERS.slice();
      // What was asked about, as names from our own lists only (a sport, a city or area), for the anonymous usage counts; never the typed text.
      const t = norm(question), sp = detectSports(t)[0], where = detectPlace(t);
      const hit = (r.items || []).length > 0;
      r.meta = {sport: sp ? sp.name : "", where: where ? where.label : "", hit, miss: MISS_KINDS.has(r.kind) || (RESULT_KINDS.has(r.kind) && !hit)};
      return r;
    }

    function route(question, ctx) {
      const t = norm(question);
      const profile = store.get() || {};
      let found = detectSports(t), loc = detectPlace(t), st = stateOf(t);
      const lines0 = [];
      if (has(t, / (forget|clear) (me|my profile|what i said|everything) /)) { store.clear(); return {kind: "profile", lines: ["Cleared. Nothing is saved in this browser now."], items: []}; }
      if (has(t, / (what did i say|what do i play|my profile|what do you remember|what do you know about me) /)) {
        return {kind: "profile", lines: Object.keys(profile).length ? ["Saved in this browser only: " + Object.entries(profile).map(([k, v]) => k + " = " + v).join(", ") + ". Say \"forget me\" to clear it."] : ["I don't have anything saved yet. Tell me, for example, \"I play padel in Reno, beginner\"."], items: []};
      }
      if (has(t, WHEN_ADD)) return whenAdd(found[0] || null, loc);
      if (has(t, WHEN_OPEN) && !has(t, / open play /)) return whenOpen(found[0] || null, loc, st, t);
      // issue 568: counts by state and by country, from the same venue data the map shows
      if (has(t, COUNT)) return countAnswer(found[0] || null, st || (has(t, / mexico /) ? "MX" : ""), t, loc);
      if (!found.length && !loc) {
        if (GREETING.test(t) || HELP.test(t)) return {kind: "welcome", lines: ["Hi! I can help you find places to play tennis, pickleball, padel, squash and other racket sports, events to watch, groups to play with, and how to try a sport.", "Tell me a sport and a city, or pick one below."], items: []};
        if (THANKS.test(t)) return {kind: "welcome", lines: ["You're welcome! Want to look for anything else?"], items: []};
        if (FRUSTRATED.test(t)) return {kind: "support", lines: ["Sorry, that wasn't what you were hoping for. I'm a simple tool that only knows what's in our venue data, so I can miss things or misread a question.", "Tell me the sport and city (for example \"padel in Reno\") and I'll try again, or pick one below."], items: []};
      }
      for (const [re, lines, items, chips] of PRODUCT) {
        if (has(t, re)) return {kind: "about", lines: lines.slice(), items: (items || []).slice(), chips: chips ? chips.slice() : undefined};
      }
      const other = !found.length && t.match(OTHER_SPORT);
      if (other) {
        const w = other[1][0].toUpperCase() + other[1].slice(1);
        return {kind: "offtopic", lines: [w + " is a bit outside what I know: RacketConnect covers racket sports like tennis, pickleball, padel, squash, badminton and table tennis.", loc ? "If you'd like to try one of those " + (loc.area ? "in " : "near ") + loc.label + ", pick one below." : "If you'd like to try one of those, tell me a city or pick one below."], items: [], chips: loc ? sportChips(loc) : undefined};
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
        else if (sp) r.chips = cityChips(sp).slice(0, 3);
        else if (loc) r.chips = sportChips(loc);
        return done(r);
      }
      if (has(t, GEAR) && !has(t, / equipment /)) {
        return done({kind: "gear", lines: ["I don't have racket-shop, restringing or rental data yet, so I won't name stores. " + (sp ? "I can show places to play " + sp.name + (loc ? (loc.area ? " in " : " near ") + loc.label : "") + " instead; some offer clinics or lessons where you can try gear. " : "") + "A ranked gear list (sport specialists first, then general sporting goods, then big-box) is planned once the data exists."], items: [], chips: sp && loc ? [sp.name + " in " + loc.label, "What is " + sp.name.toLowerCase() + "?"] : sp ? cityChips(sp).slice(0, 3) : undefined});
      }
      if (ctx && !loc && !st && has(t, VIEW) && !has(t, EVENTS) && !has(t, SOCIAL) && (!found.length || !has(t, LEARN))) return done(viewAnswer(sp, t, ctx));
      if (has(t, EVENTS)) return done(eventsAnswer(sp, loc, st, t));
      if (has(t, WALLS)) return done(wallsAnswer(sp, loc, st));
      if (has(t, SOCIAL) || has(t, SOCIAL2)) return done(socialAnswer(sp, loc, st));
      if (has(t, / paddle | paddles /) && !found.length && !has(t, / (padel|pop tennis|pickleball|beach tennis) /)) return done({kind: "clarify", lines: ["\"Paddle\" can mean a pickleball paddle, pop tennis (also called paddle tennis), or padel (a different sport on a walled court). Which one?"], items: [], chips: ["What is pickleball?", "What is pop tennis?", "What is padel?"]});
      if ((has(t, LEARN) && (found.length || has(t, / (sport|sports|racket|rackets|racquet|racquets|recommend|should i try|get started|how do i start|how do i begin|equipment|rules) /))) || (found.length && has(t, / (how do i|beginner|get started) /))) return done(learnAnswer(found, t));
      if (sp) return done(venuesAnswer(sp, loc, st, t, ""));
      if (loc && has(t, RACKET)) return done({kind: "clarify", lines: ["Which sport " + (loc.area ? "in " : "near ") + loc.label + "? For example tennis, pickleball, padel, squash or racquetball."], items: [], chips: sportChips(loc)});
      if (has(t, RACKET)) return done({kind: "clarify", lines: ["Tell me the sport and a city, for example \"pickleball in Reno\"."], items: []});
      return {kind: "refuse", lines: ["Sorry, I couldn't match that. I'm built for racket sports: where to play, events to watch, groups to play with, and how to try a sport.", "Try something like \"pickleball in Reno\", or pick one below."], items: []};
    }
    return {answer};
  }

  const api = {create, scrub, starters: STARTERS};
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.Ask = api;
})(typeof window !== "undefined" ? window : globalThis);
