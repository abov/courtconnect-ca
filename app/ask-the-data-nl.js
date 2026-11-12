// Plain-English questions -> SQL for app/ask-the-data.html. No model, no network: fixed templates plus a sport, a place and a few filters read from the
// question. The SQL is shown to the visitor and runs on the same DuckDB tables as the preset questions (app/ask-the-data-queries.json).
// Checked by ci/check_ask_the_data.py (runs chatbot/dump_ask_the_data.js, then each SQL on the export). Nothing here is sent anywhere.
(function (root) {
  "use strict";
  const norm = s => " " + String(s || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim() + " ";
  const q = s => "'" + String(s).replace(/'/g, "''") + "'"; // names come from the data's own lists, never from free text; still escaped
  const SPORT_ALIASES = {"pickle ball": "Pickleball", "racket ball": "Racquetball", "ping pong": "Table Tennis", "paddle tennis": "Pop Tennis", "poptennis": "Pop Tennis"};
  const PLACE_ALIASES = {"la": "Los Angeles", "vegas": "Las Vegas", "sf": "San Francisco", "san fran": "San Francisco"};
  const SKIP_CITY = new Set(["industry", "commerce", "mesa", "alpine", "orange", "bell", "mount", "live oak", "acme", "hope", "washington"]);
  const STATES = {california: "CA", nevada: "NV", oregon: "OR", hawaii: "HI", arizona: "AZ", mexico: "MX", "washington state": "WA", washington: "WA"};
  const STATE_NAME = {CA: "California", NV: "Nevada", OR: "Oregon", WA: "Washington", HI: "Hawaii", AZ: "Arizona", NM: "New Mexico", MX: "Mexico"};
  // places we cannot turn into one city: say so instead of searching everywhere
  const AREAS = / (bay area|silicon valley|orange county|inland empire|lake tahoe|tahoe|socal|southern california|norcal|northern california|central valley|east bay|south bay|san fernando valley|the valley|metro area|downtown) /;

  const RE = {
    count: / (how many|number of|count of|counts|total|tally) |^ count /,
    courts: / (courts?|court count) /,
    rankCities: / (cities|city|towns?) /,
    rankSports: / (sports?) /,
    rankStates: / (states?|regions?) /,
    most: / (most|top|biggest|largest|best covered|highest|popular|common|ranked?|ranking) /,
    names: / (names?|named|unnamed|nameless) /,
    checked: / (checked|verified|visited|how sure|confirmation|confirmed) /,
    howMuch: / (how much|how well|what share|what percent|what percentage|what fraction|breakdown|how sure) /,
    free: / (free|no cost|no charge) /,
    pub: / (public|open to the public) /,
    nonMember: / (non members?|nonmembers?|not members only|without membership|no membership|open to non members) /,
    membersOnly: / (members only|member only|private clubs?) /,
    website: / (website|web site|has a site|with a site) /,
    confirmedFilter: / (confirmed|verified|visited) /,
    namedFilter: / (named|with names|have names) /,
    place: / (in|near|around|at|within) /
  };

  function create(info) {
    const sportKeys = info.sports.map(n => ({key: norm(n), name: n}));
    for (const [alias, name] of Object.entries(SPORT_ALIASES)) if (info.sports.includes(name)) sportKeys.push({key: norm(alias), name});
    sportKeys.sort((a, b) => b.key.length - a.key.length);
    const cityKeys = new Map();
    for (const c of info.cities) {
      const k = norm(c);
      if (k.length > 5 && !SKIP_CITY.has(k.trim())) cityKeys.set(k, c);
    }
    const cityList = [...cityKeys.keys()].sort((a, b) => b.length - a.length);

    function detectSports(t) {
      let rest = t;
      const found = [];
      for (const s of sportKeys) {
        const pos = rest.indexOf(s.key);
        if (pos >= 0) {
          if (!found.some(f => f.name === s.name)) found.push({name: s.name, pos});
          rest = rest.slice(0, pos) + " ".repeat(s.key.length) + rest.slice(pos + s.key.length);
        }
      }
      return {sports: found.sort((a, b) => a.pos - b.pos).map(f => f.name), rest};
    }

    function detectPlace(t) {
      let city = "", state = "", rest = t;
      for (const [alias, name] of Object.entries(PLACE_ALIASES)) {
        const k = norm(alias);
        if (t.includes(k) && cityKeys.has(norm(name))) { city = cityKeys.get(norm(name)); rest = rest.replace(k, " "); break; }
      }
      if (!city) for (const k of cityList) if (t.includes(k)) { city = cityKeys.get(k); rest = rest.replace(k, " "); break; }
      for (const [n, c] of Object.entries(STATES)) {
        const k = " " + n + " ";
        if (rest.includes(k)) { state = c; rest = rest.replace(k, " "); break; }
      }
      if (!state && !city) for (const [ab, c] of [[" nv ", "NV"], [" ca ", "CA"], [" az ", "AZ"], [" wa ", "WA"], [" hi ", "HI"], [" mx ", "MX"]]) if (rest.includes(ab)) { state = c; rest = rest.replace(ab, " "); break; }
      return {city, state, rest};
    }

    // WHERE pieces on the venues table (alias v)
    function where(sel, filters) {
      const w = [];
      if (sel.city) w.push("lower(v.city) = lower(" + q(sel.city) + ")");
      if (sel.state) w.push("v.region = " + q(sel.state));
      if (filters.free) w.push("v.is_free");
      if (filters.pub) w.push("v.is_public");
      if (filters.nonMember) w.push("NOT v.members_only");
      if (filters.membersOnly) w.push("v.members_only");
      if (filters.website) w.push("v.has_website");
      if (filters.confirmed) w.push("v.confirmation IS NOT NULL");
      if (filters.named) w.push("v.name IS NOT NULL");
      return w;
    }
    const sportIn = sports => "vs.sport IN (" + sports.map(q).join(", ") + ")";
    const venueHasSport = sports => "v.venue_id IN (SELECT venue_id FROM venue_sport_names vs WHERE " + sportIn(sports) + ")";
    const whereSql = w => w.length ? " WHERE " + w.join(" AND ") : "";
    const filterWords = f => [f.free && "free", f.pub && "public", f.nonMember && "open to non-members", f.membersOnly && "members-only", f.website && "with a website", f.confirmed && "confirmed or checked by a person", f.named && "named"].filter(Boolean);

    function interpret(question) {
      const raw = String(question || "").trim();
      if (!raw) return {ok: false, message: "Type a question first."};
      let t = norm(raw);
      const sp = detectSports(t), sports = sp.sports;
      const pl = detectPlace(sp.rest), rest = pl.rest;
      const sel = {city: pl.city, state: pl.state};
      const f = {
        free: RE.free.test(t), pub: RE.pub.test(t) && !RE.nonMember.test(t), nonMember: RE.nonMember.test(t), membersOnly: RE.membersOnly.test(t),
        website: RE.website.test(t), confirmed: false, named: false
      };
      const isCount = RE.count.test(t), wantsCourts = RE.courts.test(t), isMost = RE.most.test(t);
      const asksNames = RE.names.test(t) && (RE.howMuch.test(t) || isCount || / (are|is) /.test(t));
      const asksChecked = RE.checked.test(t) && (RE.howMuch.test(t) || / (checked|verified|visited) /.test(t) && !isCount);
      if (isCount && RE.confirmedFilter.test(t) && !asksNames) f.confirmed = true;
      if (RE.namedFilter.test(t) && !/ unnamed /.test(t) && !asksNames) f.named = true;

      const read = [];
      if (sports.length) read.push("sport: " + sports.join(" + "));
      if (sel.city) read.push("city: " + sel.city + (sel.state ? ", " + STATE_NAME[sel.state] : ""));
      else if (sel.state) read.push("state: " + STATE_NAME[sel.state]);
      read.push(...filterWords(f).map(w => "only " + w));
      const readText = read.length ? "I read this as " + read.join("; ") + "." : "";

      let warn = "";
      if (!sel.city && !sel.state) {
        if (AREAS.test(t)) warn = " I can't search a wide area like that yet, so this covers every place; name a city or state to narrow it.";
        else if (RE.place.test(rest.replace(/\b(in|at)\b (the )?(world|total|all|general|database|data|export)\b/g, ""))) {
          const m = rest.match(/ (in|near|around|at|within) ([a-z0-9 ]{3,30})$/);
          if (m && !/ (the|all|total|general|each|every|my|a) /.test(" " + m[2].trim() + " ")) warn = " I didn't recognise the place after \"" + m[1] + " " + m[2].trim() + "\", so this covers every place.";
        }
      }
      const placeTitle = sel.city ? " in " + sel.city : sel.state ? " in " + STATE_NAME[sel.state] : "";
      const sportTitle = sports.length ? sports.join(" and ") : "";
      const flagNote = f.free ? "Free and public are set only where a source says so; most venues are not marked either way, so a short or empty result does not mean the rest cost money." : "";
      const out = (title, sql, note) => ({ok: true, title, sql, note: [readText, note, flagNote, warn.trim()].filter(Boolean).join(" ")});

      // 1. how sure are the names
      if (asksNames) {
        const w = where(sel, f); if (sports.length) w.push(venueHasSport(sports));
        return out("How sure are the names" + (sportTitle ? " for " + sportTitle : "") + placeTitle + "?",
          "SELECT CASE v.name_quality WHEN 'c' THEN 'Confirmed or hand-curated' WHEN 'p' THEN 'Business listing' WHEN 'i' THEN 'Inferred from a nearby park or school' ELSE 'Unnamed' END AS name_is, count(*) AS venues, round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS percent FROM venues v" + whereSql(w) + " GROUP BY v.name_quality ORDER BY venues DESC",
          "Most OpenStreetMap courts are unnamed, so many pins carry a name inferred from the park or school.");
      }
      // 2. how much has been checked
      if (asksChecked && !f.confirmed) {
        const w = where(sel, f); if (sports.length) w.push(venueHasSport(sports));
        return out("How much has anyone checked" + (sportTitle ? " (" + sportTitle + ")" : "") + placeTitle + "?",
          "SELECT CASE v.confirmation WHEN 'v' THEN 'Visited in person' WHEN 'o' THEN 'Stated by the operator' WHEN 'r' THEN 'Reported only' ELSE 'Map data only' END AS checked, count(*) AS venues FROM venues v" + whereSql(w) + " GROUP BY v.confirmation ORDER BY venues DESC",
          "Most pins are map data only. A visit, an operator's statement or a report is shown as that, and nothing stronger.");
      }
      // 3. rankings
      if (isMost && !isCount) {
        if (RE.rankCities.test(t) && !/ (which|what) sports? /.test(t)) {
          const w = where({state: sel.state}, f); if (sports.length) w.push(venueHasSport(sports));
          return out("Which cities have the most" + (sportTitle ? " " + sportTitle : "") + " venues" + (sel.state ? " in " + STATE_NAME[sel.state] : "") + "?",
            "SELECT v.region, v.city, count(*) AS venues FROM venues v" + whereSql(w) + " GROUP BY v.region, v.city ORDER BY venues DESC, v.city LIMIT 15",
            "City names come from the data sources, and each pin has one.");
        }
        if (RE.rankStates.test(t) && !RE.rankSports.test(t)) {
          const w = where({city: sel.city}, f); if (sports.length) w.push(venueHasSport(sports));
          return out("Which states have the most" + (sportTitle ? " " + sportTitle : "") + " venues?",
            "SELECT v.region, count(*) AS venues FROM venues v" + whereSql(w) + " GROUP BY v.region ORDER BY venues DESC",
            "Region codes: CA California, NV Nevada, OR Oregon, WA Washington, AZ Arizona, NM New Mexico, HI Hawaii, MX Mexico (pilot).");
        }
        if (RE.rankSports.test(t) && !sports.length) {
          const w = where(sel, f); w.unshift("vs.shares_courts_with IS NULL");
          return out("Which sports have the most venues" + placeTitle + "?",
            "SELECT vs.sport, count(*) AS venues FROM venue_sport_names vs JOIN venues v USING (venue_id)" + whereSql(w) + " GROUP BY vs.sport ORDER BY venues DESC, vs.sport LIMIT 15",
            "One row per sport at a venue, so a venue with tennis and pickleball counts once for each. Sports played on another sport's courts are left out so they don't repeat the tennis count.");
        }
      }
      // 4. counts
      if (isCount) {
        if (wantsCourts) {
          const w = where(sel, f);
          if (sports.length) {
            w.unshift(sportIn(sports));
            return out("How many " + sportTitle + " courts are known" + placeTitle + "?",
              "SELECT vs.sport, sum(vs.courts) AS courts_mapped, count(*) FILTER (WHERE vs.courts > 0) AS venues_with_count, count(*) FILTER (WHERE vs.courts = 0) AS venues_count_unknown FROM venue_sport_names vs JOIN venues v USING (venue_id)" + whereSql(w) + " GROUP BY vs.sport ORDER BY courts_mapped DESC",
              "Mapped courts only, as OpenStreetMap or a person gave them. A count of 0 means unknown, not none, so those venues are listed separately.");
          }
          w.unshift("vs.shares_courts_with IS NULL");
          return out("How many courts are known, by sport" + placeTitle + "?",
            "SELECT vs.sport, sum(vs.courts) AS courts_mapped, count(*) FILTER (WHERE vs.courts > 0) AS venues_with_count, count(*) FILTER (WHERE vs.courts = 0) AS venues_count_unknown FROM venue_sport_names vs JOIN venues v USING (venue_id)" + whereSql(w) + " GROUP BY vs.sport ORDER BY courts_mapped DESC, vs.sport LIMIT 15",
            "Mapped courts only, for sports with courts of their own. A count of 0 means unknown, not none.");
        }
        const w = where(sel, f); if (sports.length) w.push(venueHasSport(sports));
        return out("How many " + (sportTitle ? sportTitle + " " : "") + "venues" + placeTitle + "?",
          "SELECT count(*) AS venues FROM venues v" + whereSql(w),
          "Counts what the export lists, not every court there is. A venue that lists a sport is not proof it can be booked or played there today.");
      }
      // 5. list venues (needs a sport)
      if (sports.length && !isMost) {
        const w = where(sel, f); w.unshift(sportIn(sports));
        return out("Where can I play " + sportTitle + placeTitle + "?",
          "SELECT coalesce(v.name, '(unnamed)') AS venue, v.city, v.region, " + (sports.length > 1 ? "vs.sport, " : "") + "v.name_quality, vs.courts, v.is_free, v.members_only, v.confirmation FROM venue_sport_names vs JOIN venues v USING (venue_id)" + whereSql(w) + " ORDER BY v.region, v.city, venue LIMIT 25",
          "First 25 by state and city. name_quality: c confirmed or curated, p business listing, i name inferred from a nearby park or school, u unnamed. courts 0 means unknown. confirmation: v visited, o stated by the operator, r reported; blank means map data only.");
      }
      // 6. a place with no sport: counts by sport there
      if ((sel.city || sel.state) && !sports.length) {
        const w = where(sel, f); w.unshift("vs.shares_courts_with IS NULL");
        return out("What is there" + placeTitle + "?",
          "SELECT vs.sport, count(*) AS venues FROM venue_sport_names vs JOIN venues v USING (venue_id)" + whereSql(w) + " GROUP BY vs.sport ORDER BY venues DESC, vs.sport LIMIT 15",
          "Venues per sport" + placeTitle + ". Add a sport to the question to list the venues.");
      }
      return {ok: false, message: "I couldn't turn that into a query. I can list venues for a sport (\"padel in Las Vegas\"), count them (\"how many free pickleball courts in Reno\"), rank cities, states or sports (\"which cities have the most squash\"), and show how sure the names are or how much has been checked. Name a sport, a city or a state."};
    }
    return {interpret};
  }

  const api = {create, EXAMPLES: [
    "Where can I play padel in Las Vegas?",
    "How many pickleball courts are in Reno?",
    "Which cities have the most squash venues?",
    "Public tennis courts in Los Angeles",
    "Which sports have the most venues in Oregon?",
    "How sure are the names in Seattle?"
  ]};
  if (typeof module === "object" && module.exports) module.exports = api; else root.AskTheDataNL = api;
})(typeof window !== "undefined" ? window : globalThis);
