// Runs the 30 questions of docs/chatbot_questions.md through the free ask box (app/ask.js) and checks the kind of answer.
//   node chatbot/test_ask.js          (prints each answer; exit code 1 if a check fails)
const fs = require("fs");
const path = require("path");
const Ask = require("../app/ask.js");

const root = path.join(__dirname, "..", "app", "data");
const data = JSON.parse(fs.readFileSync(path.join(root, "venues.json"), "utf8"));
let saved = {};
const store = {get: () => saved, set: v => { saved = v; }, clear: () => { saved = {}; }};

// [question, expected kind(s), text that must appear (optional)]
const Q = [
  ["Where can I play pickleball in Reno?", "venues", "Neil Road"],
  ["Free public tennis courts near Santa Monica?", "venues", "marked free"],
  ["Is there a padel court in Las Vegas?", "venues", "P1 Padel"],
  ["Where can I play racquetball in San Diego?", "venues", "LA Fitness San Diego ("],
  ["Any squash courts in the Bay Area open to non-members?", "venues", "members-only"],
  ["Where can I hit against a wall in Oakland?", "walls"],
  ["Closest badminton courts to Sacramento?", "venues"],
  ["Is there pop tennis in LA?", "venues"],
  ["Are there lit courts for evening tennis in Henderson?", "venues", "· lit"],
  ["Where can I play beach tennis in California?", "venues|clarify"],
  ["Any tennis tournaments I can watch near Redding this fall?", "events"],
  ["Where can I watch pro pickleball in Nevada?", "events"],
  ["Is anything on this weekend in Bakersfield?", "events"],
  ["Where can I watch tennis on a big screen?", "events", "big screen"],
  ["What is padel and how is it different from pickleball?", "learn", "walls"],
  ["What sport should I try if I like tennis but want something easier on the knees?", "learn", "doctor"],
  ["What is pop tennis vs paddle tennis?", "learn", "same sport"],
  ["How do I get started with squash?", "learn", "Squash"],
  ["What equipment do I need for racquetball?", "learn", "Racket, rubber ball"],
  ["Is badminton the same as pickleball?", "learn", "Badminton"],
  ["Where can I buy a pickleball paddle in San Diego?", "gear", "won't name stores"],
  ["Where can I get a tennis racket restrung near me (Berkeley)?", "gear", "won't name stores"],
  ["Can I rent a padel racket before buying?", "gear", "won't name stores"],
  ["Cheapest place to try a squash racket?", "gear", "won't name stores"],
  ["Rank the racket shops in Las Vegas from most to least useful for pickleball.", "gear", "won't name stores"],
  ["Which store has the best deals?", "gear", "won't name stores"],
  ["MULTI", "venues", "Using your saved"],
  ["NEWSESSION", "profile", "Padel"],
  ["Write me a cover letter.", "refuse"],
  ["Book me a court at 6pm tomorrow.", "booking", "can't book"],
  // extras beyond the 30 in docs/chatbot_questions.md: other states, social groups, wall pins
  ["Where can I play badminton in Seattle?", "venues", " WA "],
  ["Pickleball in Honolulu", "venues", " HI "],
  ["Who can I play tennis with near Seattle?", "social"],
  ["Any pickleball leagues in Portland?", "social"],
  ["Where is a hitting wall in Oregon?", "walls", " OR"],
  // kind replies: greetings, thanks, frustration, other sports, off-topic (each must offer chips, never the old cold refusal)
  ["Hi", "welcome", "Hi!"],
  ["hello there", "welcome"],
  ["What can you do?", "welcome"],
  ["Thanks!", "welcome", "welcome"],
  ["This is useless", "support", "Sorry"],
  ["Where can I play golf?", "offtopic", "Golf"],
  ["Basketball courts in Reno", "offtopic", "near Reno"],
  ["What's the weather in Reno?", "refuse", "couldn't match"],
];

let ask = Ask.create(data, store), fails = 0;
Q.forEach(([q, kind, must], i) => {
  let r;
  if (q === "MULTI") {
    saved = {};
    ask.answer("I play padel in Reno, beginner");
    q = "[after \"I play padel in Reno, beginner\"] Where should I play?";
    r = ask.answer("Where should I play?");
  } else if (q === "NEWSESSION") {
    ask = Ask.create(data, store); // new page load, same browser storage
    q = "[new session] What did I say I play?";
    r = ask.answer("What did I say I play?");
  } else { saved = {}; r = ask.answer(q); } // each question starts without a saved profile
  const text = [...r.lines, ...r.items.map(x => x.title + " | " + x.detail)].join("\n");
  // no result list means a next step: chips; and the old cold refusal text is gone
  const kindly = !text.includes("I only help with") && ((r.items || []).length > 0 || (r.chips || []).length > 0);
  const ok = kind.split("|").includes(r.kind) && (!must || text.includes(must)) && kindly;
  if (!ok) fails++;
  console.log(`\n${ok ? "PASS" : "FAIL"} ${i + 1}. ${q}  [${r.kind}]`);
  console.log(text.split("\n").slice(0, 4).map(l => "   " + l.slice(0, 230)).join("\n"));
});
console.log(`\n${Q.length - fails}/${Q.length} passed`);
process.exit(fails ? 1 : 0);
