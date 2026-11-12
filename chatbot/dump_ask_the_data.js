// Prints, as JSON, what the plain-English box (app/ask-the-data-nl.js) makes of each test question in app/ask-the-data-questions.json.
// ci/check_ask_the_data.py runs the SQL it prints on the export. Lists of sports and cities come from venues.json the same way the page gets them from its tables.
//   node chatbot/dump_ask_the_data.js
const fs = require("fs");
const path = require("path");
const NL = require("../app/ask-the-data-nl.js");
const app = path.join(__dirname, "..", "app");
const data = JSON.parse(fs.readFileSync(path.join(app, "data", "venues.json"), "utf8"));
const cases = JSON.parse(fs.readFileSync(path.join(app, "ask-the-data-questions.json"), "utf8")).cases;
const used = new Set();
data.venues.forEach(v => (v.p || []).forEach(p => used.add(p[0])));
const sports = [...used].map(i => data.sports[i].n);
const cities = [...new Set(data.venues.map(v => v.c).filter(Boolean))];
const nl = NL.create({sports, cities});
console.log(JSON.stringify(cases.map(c => ({question: c.question, expect: c.expect, result: nl.interpret(c.question)}))));
