// Instagram sweep snippet (ADR 0009 amendment, 2026-10-19). Paste into the built-in browser pane's JS tool
// AFTER navigating to https://www.instagram.com/<handle>/ (logged out; ignore the log-in banner, never sign in).
// Run it for 3-4 accounts per call (a script must finish in 45 s). It reads the profile's ~12 recent post links,
// fetches each post page without cookies, and returns only posts dated on/after SINCE that look like events.
// Store facts only (name, date, venue, link). Never store captions, images, counts or comments.
await new Promise(r => setTimeout(r, 2500));
const SINCE = new Date('2026-10-01');   // set to ~3 weeks before the run date
const KW = /tournament|\bopen\b|cup|championship|league|series|register|sign.?up|round.?robin|clash|classic|finals|bt10|bt50|nov(ember)?\b|dec(ember)?\b|jan(uary)?\b|2027|save the date|coming soon|opening|americano|mixer|event/i;
const links = [...new Set([...document.querySelectorAll('a[href*="/p/"],a[href*="/reel/"]')].map(a => a.getAttribute('href')))].slice(0, 12);
const res = await Promise.all(links.map(async h => {
  try {
    const t = await (await fetch(h, { credentials: 'omit' })).text();
    const d = (t.match(/property="og:description" content="([^"]*)"/) || [])[1] || '';
    const c = d.replace(/&quot;/g, '"').replace(/&#0?39;|&#x27;/g, "'").replace(/&#x[0-9a-f]+;/g, '').replace(/&#064;/g, '@').replace(/&amp;/g, '&').replace(/\s+/g, ' ');
    const m = c.match(/ on ([A-Z][a-z]+ \d+, \d{4})/);   // the post date; a caption without a year is that post's year
    return { id: h.split('/').filter(Boolean).slice(-1)[0], date: m ? m[1] : '?', ok: !!m && new Date(m[1]) >= SINCE && KW.test(c), c: c.slice(c.indexOf('"') + 1, c.indexOf('"') + 300) };
  } catch (e) { return { id: h, ok: false, c: 'ERR' }; }
}));
({ acct: location.pathname, n: links.length, latest: res.map(r => r.date).slice(0, 3), kept: res.filter(r => r.ok).map(r => r.id + ' | ' + r.date + ' | ' + r.c) });
