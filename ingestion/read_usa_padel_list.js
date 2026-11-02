// Reads the official USA Padel tournament list (Nox USA Padel Circuit) with the headless Chromium the cloud
// sandbox ships. The list loads by script and is paged (15 a page), so plain fetches see nothing.
// Public page, logged out, facts only (name, city, dates, registration status; no organizer names, no entries).
// Usage:  NODE_PATH=$(npm root -g) node ingestion/read_usa_padel_list.js   -> TSV: name, city, dates, status
// Match rows to watch_events.csv by club name; keep rows whose city is in CA/NV. A tournament missing from this
// list is NOT confirmed (do not re-date it). Source: docs/tournament_run_parts.md, Part 3.
const { chromium } = require('playwright');
const URL = 'https://uspa-tournaments.worldpadelrating.com/en-US/tournaments?country=US';
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto(URL, { waitUntil: 'networkidle', timeout: 45000 }).catch(() => {});
  await p.click('text=Reject all').catch(() => {});
  const seen = new Set(), rows = [];
  for (let pg = 1; pg <= 10; pg++) {
    await p.waitForTimeout(2500);
    const lines = (await p.innerText('body')).split('\n').map(s => s.trim());
    for (let i = 3; i < lines.length - 2; i++) {
      // card layout: name, circuit, sport, city, dates, status
      if (lines[i] === 'Padel' && /^[A-Z][a-z]{2} \d+ - /.test(lines[i + 2] || '')) {
        const r = [lines[i - 2], lines[i + 1], lines[i + 2], lines[i + 3] || ''].join('\t');
        if (!seen.has(r)) { seen.add(r); rows.push(r); }
      }
    }
    const next = await p.$('[aria-label*="next" i]');
    if (!next || await next.isDisabled().catch(() => true)) break;
    await next.click().catch(() => {});
  }
  console.log(rows.join('\n'));
  if (!rows.length) { console.error('NO ROWS: list did not load; treat as a failed source'); process.exitCode = 1; }
  await b.close();
})();
