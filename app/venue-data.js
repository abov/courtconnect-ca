// Turns data/map.json (pins, list, search, filters) and data/details.json (ids, addresses, website links, notes) back into
// the venue objects of data/venues.json. ingestion/split_app_data.py writes both files; ci/test_split_data.js checks the round trip.
// Browser: window.VenueData; Node: require("../app/venue-data.js").
(function (root) {
  const SCALE = 100000;   // same as split_app_data.py
  const RESERVED = new Set(["len", "q", "dy", "dx", "w"]);

  function fill(out, cols, skip) {   // dense columns are lists, the rest {index: value}; a missing key stays missing
    for (const [k, col] of Object.entries(cols)) {
      if (skip.has(k)) continue;
      if (Array.isArray(col)) for (let n = 0; n < out.length; n++) out[n][k] = col[n];
      else for (const n in col) out[+n][k] = col[n];
    }
  }

  // map.json -> {doc, venues}: doc has every top-level list of venues.json, with `venues` rebuilt; `w` is 1 until details arrive
  function decodeCore(core) {
    const c = core.vc, n = c.len, venues = new Array(n);
    let y = 0, x = 0;
    for (let k = 0; k < n; k++) {
      y += c.dy[k]; x += c.dx[k];
      venues[k] = {q: c.q[k], y: y / SCALE, x: x / SCALE};
    }
    fill(venues, c, RESERVED);
    for (const k of c.w) venues[k].w = 1;
    const doc = {};
    for (const [k, v] of Object.entries(core)) if (k !== "vc") doc[k] = v;
    doc.venues = venues;
    return doc;
  }

  // details.json merged into the same objects (in place, so every holder of a venue sees it)
  function mergeDetails(venues, det) {
    if (det.len !== venues.length) throw new Error("details.json does not match map.json (" + det.len + " vs " + venues.length + " venues)");
    fill(venues, det, new Set(["len"]));
  }

  root.VenueData = {decodeCore, mergeDetails};
  if (typeof module !== "undefined") module.exports = root.VenueData;
})(typeof window !== "undefined" ? window : globalThis);
