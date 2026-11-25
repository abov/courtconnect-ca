// Checks that data/map.json + data/details.json (ingestion/split_app_data.py) rebuild data/venues.json exactly, through the same
// decoder the map uses (app/venue-data.js), and prints what a phone downloads and parses before the map can show pins.
//   python ingestion/split_app_data.py && node ci/test_split_data.js
// Timing is an estimate, not a field measurement: download at Lighthouse's mobile test speed (1.6 Mbps, 150 ms round trip),
// parse time measured here and multiplied by 4 (Lighthouse's phone CPU slowdown).
const fs = require("fs"), path = require("path"), zlib = require("zlib"), assert = require("assert");
const VenueData = require("../app/venue-data.js");
const dir = path.join(__dirname, "..", "app", "data");
const read = f => fs.readFileSync(path.join(dir, f), "utf8");

const fullText = read("venues.json"), coreText = read("map.json"), detText = read("details.json");
const full = JSON.parse(fullText);
const doc = VenueData.decodeCore(JSON.parse(coreText));
for (const k of Object.keys(full)) if (k !== "venues") assert.deepStrictEqual(doc[k], full[k], "map.json lost or changed " + k);
assert.strictEqual(Object.keys(doc).length, Object.keys(full).length, "map.json has extra top-level keys");
// before details: what the pins, list and filters read must already be there
const CORE_KEYS = ["n", "c", "r", "q", "y", "x", "f", "p", "o"];
doc.venues.forEach((v, n) => { for (const k of CORE_KEYS) assert.deepStrictEqual(v[k], full.venues[n][k], "venue " + n + " field " + k); assert.strictEqual(!!v.w, !!full.venues[n].w, "venue " + n + " website flag"); });
VenueData.mergeDetails(doc.venues, JSON.parse(detText));
assert.strictEqual(doc.venues.length, full.venues.length);
doc.venues.forEach((v, n) => assert.deepStrictEqual(v, full.venues[n], "venue " + n + " (" + full.venues[n].i + ") differs after details"));
console.log("map.json + details.json rebuild venues.json exactly (" + doc.venues.length + " venues).");

if (process.argv.includes("--measure")) {
  const gz = t => zlib.gzipSync(Buffer.from(t), {level: 6}).length;   // GitHub Pages serves JSON gzipped
  const BPS = 1638.4 * 1000 / 8, RTT = 0.15, CPU = 4;
  const time = (fn, reps = 5) => { fn(); const t = process.hrtime.bigint(); for (let i = 0; i < reps; i++) fn(); return Number(process.hrtime.bigint() - t) / 1e6 / reps; };
  const before = {gz: gz(fullText), ms: time(() => { const d = JSON.parse(fullText); d.venues.forEach(v => v.m = v.p.reduce((a, p) => a | p[2], 0)); })};
  const after = {gz: gz(coreText), ms: time(() => VenueData.decodeCore(JSON.parse(coreText)).venues.forEach(v => v.m = v.p.reduce((a, p) => a | p[2], 0)))};
  const kb = b => Math.round(b / 1000) + " KB", s = x => x.toFixed(1) + " s";
  for (const [name, r] of [["before: venues.json", before], ["after:  map.json", after]])
    console.log(name + "  " + kb(r.gz) + " gzip, download ~" + s(RTT + r.gz / BPS) + ", parse ~" + s(r.ms * CPU / 1000) + " (phone estimate)");
  console.log("later:  details.json " + kb(gz(detText)) + " gzip, fetched after the map shows or when a place is opened");
}
