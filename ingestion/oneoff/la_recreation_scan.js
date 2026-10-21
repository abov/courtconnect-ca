/* Scan the City of LA Recreation and Parks site for racket-sport facility features.

   recreation.parks.lacity.gov answers 403 to scripts (Python, curl), so this runs INSIDE the browser pane, as a same-origin fetch:
     1. Open https://recreation.parks.lacity.gov/ in the Browser pane (any page of the site).
     2. Run this file's contents with javascript_tool (it starts a background scan and returns at once).
     3. Poll `({done: window.__laScan.done, total: window.__laScan.total, fin: window.__laScan.fin})` every ~40 s (about 3 min for ~400 pages).
     4. When fin is true, read `window.__laScan.csv` and save it as ingestion/data/la_recreation_scan.csv.
     5. python ingestion/oneoff/la_recreation_scan.py   (joins coordinates from the city's open-data list, compares to the map, writes the gap report)

   Reads only public pages: the sitemap, then each /park/, /reccenter/ and /sports/tennis/facility/ page. One request per 0.4 s.
   Each page has a "Facility Features" list (comma-separated, e.g. "Tennis Courts (Lighted) , Handball Courts (Lighted) , Pickleball").
   The list gives no court count and no wall count, so handball means "handball court, walls unknown".
*/
window.__laScan = {done: 0, total: 0, errors: [], rows: [], csv: "", fin: false};
(async () => {
  const S = window.__laScan;
  const sm = await (await fetch("/sitemap.xml")).text();
  const urls = [...sm.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => m[1].replace(/&amp;/g, "&"))
    .filter(u => /\/(park|reccenter)\/[^\/?#]+$|\/sports\/tennis\/facility\/[^\/?#]+$/.test(u));
  S.total = urls.length;
  const RACKET = /tennis|handball|paddle|pickleball|racquet|squash|badminton|ping/i;
  for (const u of urls) {
    const path = u.replace(/^https?:\/\/[^\/]+/, "");
    try {
      const r = await fetch(path);
      if (!r.ok) throw new Error("HTTP " + r.status);
      const d = new DOMParser().parseFromString(await r.text(), "text/html");
      const label = [...d.querySelectorAll(".field-label")].find(e => /^\s*Facility Features\s*$/i.test(e.textContent));
      const items = label && label.parentElement.querySelector(".field-items")
        ? label.parentElement.querySelector(".field-items").textContent.split(",").map(s => s.replace(/\s+/g, " ").trim()).filter(Boolean) : [];
      S.rows.push({path, hasFeatures: !!label, racket: items.filter(i => RACKET.test(i))});
    } catch (e) { S.errors.push(path + " " + e.message); }
    S.done++;
    await new Promise(r => setTimeout(r, 400));
  }
  S.csv = "path,has_features,racket_features\n" + S.rows.map(r => [r.path, r.hasFeatures ? 1 : 0, '"' + r.racket.join(" | ") + '"'].join(",")).join("\n") + "\n";
  S.fin = true;
})();
"started";
