---
title: RacketConnect data-quality scorecard
---

```sql stats
select * exclude (as_of, map_as_of), strftime(cast(as_of as date), '%Y-%m-%d') as as_of, strftime(cast(map_as_of as date), '%Y-%m-%d') as map_as_of
from courtconnect.stats
```

```sql trend
select cast(date as date) as date, venues, tests_pass, sla_met, sla_total
from courtconnect.trend
order by 1
```

```sql venue_trend
select date, venues from ${trend}
union all
select cast(map_as_of as date), map_venues from courtconnect.stats
where cast(map_as_of as date) > (select max(date) from ${trend})
order by 1
```

```sql coverage
select sport, venues, status
from courtconnect.sport_coverage
order by venues desc, sport
```

```sql status_counts
select status, count(*) as sports, sum(venues) as venues
from courtconnect.sport_coverage
group by 1
order by 2 desc
```

```sql issues
select cast(date as date) as date, opened, closed, open_now,
  sum(opened) over (order by date) as opened_total,
  sum(closed) over (order by date) as closed_total
from courtconnect.issues order by 1
```

```sql issue_totals
select sum(opened) as opened, sum(closed) as closed, max_by(open_now, date) as open_now from courtconnect.issues
```

```sql views
select cast(day as date) as day, page_views, events from courtconnect.views order by 1
```

```sql view_totals
select sum(page_views) as page_views, sum(events) as events, count(*) as days from courtconnect.views
```

```sql ask_totals
select
  coalesce(sum(count) filter (where event = 'ask-kind'), 0) as questions,
  coalesce(sum(count) filter (where event = 'ask-kind' and detail in ('refuse', 'offtopic', 'clarify', 'support')), 0) as unmatched,
  coalesce(sum(count) filter (where event = 'ask-open'), 0) as opens,
  coalesce(sum(count) filter (where event = 'ask-empty'), 0) as empty_results
from courtconnect.events
```

```sql ask_daily
select cast(day as date) as day, sum(count) as questions
from courtconnect.events where event = 'ask-kind' group by 1 order by 1
```

```sql ask_kinds
select detail as reply, sum(count) as questions
from courtconnect.events where event = 'ask-kind' group by 1 order by 2 desc
```

```sql ask_sports
select detail as sport, sum(count) as questions
from courtconnect.events where event = 'ask-sport' group by 1 order by 2 desc limit 10
```

```sql ask_places
select detail as place, sum(count) as questions
from courtconnect.events where event = 'ask-where' group by 1 order by 2 desc limit 10
```

```sql sport_view
select sport, venues, completeness, hand_checked_share, picks, linkouts, asks, demand,
  demand * 1.0 / nullif(sum(demand) over (), 0) as demand_share,
  demand * 1.0 / nullif(sum(demand) over (), 0) * (1 - completeness) as verify_score
from courtconnect.sport_scorecard
order by verify_score desc nulls last, venues desc
```

```sql sport_popular
select * from ${sport_view} order by demand desc, venues desc limit 10
```

```sql city_watched
select city, region, venues, completeness, hand_checked_share, opens
from courtconnect.city_scorecard where opens > 0 order by opens desc, venues desc limit 10
```

```sql city_thin
select city, region, venues, private_pins, completeness, real_name_share, address_share, website_share
from courtconnect.city_scorecard where venues - private_pins >= 50 order by completeness, venues desc limit 10
```

```sql interest_gaps
select metro, sport, interest_index, venues, completeness_share
from courtconnect.search_interest
where gap_candidate order by interest_index desc, venues
```

```sql interest_all
select sport, metro, interest_index, interest_rank, venues, completeness_share
from courtconnect.search_interest
where confidence = 'ok' order by sport, interest_index desc
```

```sql interest_meta
select strftime(max(cast(exported_on as date)), '%Y-%m-%d') as exported_on from courtconnect.search_interest
```

```sql ml_latest
select * from courtconnect.ml_metrics order by date desc limit 1
```

```sql ml_history
select cast(date as date) as date, loo_accuracy, likely_right
from courtconnect.ml_metrics order by 1
```

```sql ml_span
select
  arg_max(labels, loo_accuracy) as peak_labels, max(loo_accuracy) as peak_accuracy,
  arg_max(labels, date) as last_labels, arg_max(loo_accuracy, date) as last_accuracy,
  arg_max(likely_right, date) as last_likely_right
from courtconnect.ml_metrics
```

```sql queue_guess
select model_guess, sum(rows) as rows from courtconnect.review_queue group by 1 order by 2 desc
```

```sql queue_sport
select sport, sum(rows) as rows from courtconnect.review_queue group by 1 order by 2 desc limit 8
```

```sql reader_sums
select sum(facts) as facts, sum(facts) filter (where outcome = 'agree') as agree, sum(facts) filter (where outcome = 'new') as new_facts
from courtconnect.reader_outcomes
```

[Map](https://abov.github.io/courtconnect-ca/) · [How it's built](https://abov.github.io/courtconnect-ca/how-its-built.html) · **Data quality** · [Docs](https://abov.github.io/courtconnect-ca/how-its-built.html#docs) · [Run history](https://abov.github.io/courtconnect-ca/run-history.html) · [Ask the data](https://abov.github.io/courtconnect-ca/ask-the-data.html) · [Source](https://github.com/abov/courtconnect-ca)

How complete the RacketConnect data is. Counts only; no venue details are shown.

### The map, as of {stats[0].map_as_of}

<BigValue data={stats} value=map_venues title="Venues on the map" fmt=num0 />
<BigValue data={stats} value=map_sports_with_venues title="Sports with a venue" />

{stats[0].map_sports_with_venues} of {stats[0].map_sports_total} sports have a venue. These two numbers come straight from the map's data file.

### Quality checks, as of {stats[0].as_of}

<BigValue data={stats} value=sla_met title="Service levels met" />
<BigValue data={stats} value=gold_wrong_merges title="Wrong merges in the gold set" />

{stats[0].sla_met} of {stats[0].sla_total} service levels are met. These are re-measured at each refresh.

## Trend, one point per refresh

One point per refresh, so the lines are short for now.

<LineChart data={venue_trend} x=date y=venues title="Venues on the map" yAxisTitle="Venues" />

The scorecard and the map count venues the same way. The scorecard is re-run at each refresh, so its last point can be older than the map; the newest point here is the map's own count above.

## Feedback issues, open and closed

Reports sent through the map's forms, as GitHub issues. Updated daily.

<BigValue data={issue_totals} value=open_now title="Open now" />
<BigValue data={issue_totals} value=opened title="Opened, all time" />
<BigValue data={issue_totals} value=closed title="Closed, all time" />

<LineChart data={issues} x=date y={["opened_total","closed_total"]} title="Issues opened vs closed, running total" yAxisTitle="Issues" />

The gap between the two lines is the number of issues still open.

## Site views over time

{view_totals[0].page_views} page views and {view_totals[0].events} clicks over {view_totals[0].days} days. Anonymous and approximate: ad blockers hide some visits.

<LineChart data={views} x=day y={["page_views","events"]} title="Page views and events per day" />

## Are people finding what they ask for?

Counts from the map's ask box, which has no AI model behind it. Only the kind of reply, whether it found anything, and the sport and place it was about are counted. The question text is never sent. Anonymous and approximate.

{#if ask_totals[0].questions > 0}

<BigValue data={ask_totals} value=opens title="Times opened" fmt=num0 />
<BigValue data={ask_totals} value=questions title="Questions asked" fmt=num0 />
<BigValue data={ask_totals} value=unmatched title="Not understood or off topic" fmt=num0 />
<BigValue data={ask_totals} value=empty_results title="Searches with no results" fmt=num0 />

<LineChart data={ask_daily} x=day y=questions title="Questions per day" />

<BarChart data={ask_kinds} x=reply y=questions title="What kind of reply each question got" swapXY=true />

Many "refuse" or "clarify" replies mean people ask things the box does not handle yet; those are the next rules to write. "Searches with no results" are places or sports people asked for that the map does not have.

<DataTable data={ask_sports} rows=10>
  <Column id=sport title="Sport asked about" />
  <Column id=questions fmt=num0 />
</DataTable>

<DataTable data={ask_places} rows=10>
  <Column id=place title="Place asked about" />
  <Column id=questions fmt=num0 />
</DataTable>

{:else}

No questions counted yet. Counting starts when this release reaches the live map, so this section fills in as people use the ask box.

{/if}

## Accuracy against popularity

Popularity is what visitors do on the map: pick a sport, click out, ask about it. Traffic is small, so read it as a direction, not a ranking. Completeness is the average share of venues with a real name, a street address and a website. Pins that are likely private residence courts (unnamed, not known to be public; they never get a street, for privacy) are left out of that share and counted in "Private pins", so a neighbourhood of backyard courts does not read as bad data. "Hand-checked" is the share someone visited or the operator confirmed. Sports assumed playable on tennis courts are left out, because they repeat the tennis venues.

<BarChart data={sport_popular} x=sport y=completeness title="Completeness of the most-used sports" yFmt=pct0 yMin=0 yMax=1 />

The table is ordered by a verify-next score: a sport's share of all demand, times how incomplete its venues are. High demand with low completeness comes first.

<DataTable data={sport_view} rows=12 search=true>
  <Column id=sport />
  <Column id=venues fmt=num0 />
  <Column id=completeness fmt=pct0 contentType=colorscale colorScale=#6fb27c />
  <Column id=hand_checked_share title="Hand-checked" fmt=pct0 />
  <Column id=picks title="Picks" />
  <Column id=linkouts title="Link-outs" />
  <Column id=asks title="Asked" />
  <Column id=verify_score title="Verify next" fmt=num3 contentType=colorscale colorScale=#e9a23b />
</DataTable>

### By place

Cities where visitors opened a venue, then the biggest cities that are the least complete. One visitor opening one city is not a trend; the second table does not depend on traffic.

<DataTable data={city_watched} rows=10>
  <Column id=city />
  <Column id=region />
  <Column id=venues fmt=num0 />
  <Column id=completeness fmt=pct0 contentType=colorscale colorScale=#6fb27c />
  <Column id=hand_checked_share title="Hand-checked" fmt=pct0 />
  <Column id=opens title="Venue opens" />
</DataTable>

<DataTable data={city_thin} rows=10>
  <Column id=city title="Least complete cities with 50+ non-private venues" />
  <Column id=region />
  <Column id=venues fmt=num0 />
  <Column id=private_pins title="Private pins" fmt=num0 />
  <Column id=completeness fmt=pct0 contentType=colorscale colorScale=#6fb27c />
  <Column id=real_name_share title="Real name" fmt=pct0 />
  <Column id=address_share title="Address" fmt=pct0 />
  <Column id=website_share title="Website" fmt=pct0 />
</DataTable>

## Search interest against coverage

An outside signal for popularity: how much people in each metro search Google for a sport, next to what we list there (Google Trends, exported {interest_meta[0].exported_on}, refreshed about quarterly). The index is relative and sampled: 100 is the metro with the most searches for that sport, so compare metros within one sport, never one sport with another. It is not a count of players. Venues are assigned to the nearest metro anchor city within 120 miles, our own approximation, so border and rural pins can land in the wrong metro. Yuma-El Centro also includes Arizona searches, so a gap there is weak. A gap is a place to look for missing venues, not proof of one.

High interest and 3 or fewer venues:

<DataTable data={interest_gaps} rows=12>
  <Column id=metro />
  <Column id=sport />
  <Column id=interest_index title="Interest" fmt=num0 contentType=colorscale colorScale=#e9a23b />
  <Column id=venues fmt=num0 />
  <Column id=completeness_share title="Completeness" fmt=pct0 />
</DataTable>

All metros, by sport (the five busiest sports; thin Trends data is left out):

<DataTable data={interest_all} rows=15 search=true>
  <Column id=sport />
  <Column id=metro />
  <Column id=interest_index title="Interest" fmt=num0 contentType=colorscale colorScale=#e9a23b />
  <Column id=interest_rank title="Rank" />
  <Column id=venues fmt=num0 contentType=colorscale colorScale=#6fb27c />
  <Column id=completeness_share title="Completeness" fmt=pct0 contentType=colorscale colorScale=#6fb27c />
</DataTable>

## What the machine learning is doing

Two small models help with the review work. Neither one changes the map: a person confirms every fact.

<BigValue data={ml_latest} value=loo_accuracy title="Ranker accuracy" fmt=pct0 />
<BigValue data={ml_latest} value=loo_auc title="Ranker AUC (1 is perfect)" fmt=num2 />
<BigValue data={ml_latest} value=labels title="Human verdicts it learns from" fmt=num0 />
<BigValue data={ml_latest} value=queue_rows title="Rows waiting for review" fmt=num0 />

The review-queue ranker guesses which uncertain sport labels are right, so the clearest cases are checked first. Each score is measured by "leave-one-out" testing: for every human verdict, the model is retrained without that verdict and asked to predict it, so it is never graded on an answer it has seen. Accuracy counts every verdict; "likely right" counts only the calls the model was confident about.

<LineChart data={ml_history} x=date y={["loo_accuracy","likely_right"]} title="Ranker score over time" yFmt=pct0 yMin=0 yMax=1 />

Accuracy peaked at <Value data={ml_span} column=peak_accuracy fmt=pct0 /> with <Value data={ml_span} column=peak_labels fmt=num0 /> verdicts and now stands at <Value data={ml_span} column=last_accuracy fmt=pct0 /> with <Value data={ml_span} column=last_labels fmt=num0 /> verdicts in total. The newer verdicts are mostly padel, academies and clubs, which may be harder to tell apart, though we have not tested that. When the model rates a label "likely right", it is right <Value data={ml_span} column=last_likely_right fmt=pct0 /> of the time, so it still helps put the clearest cases first. It is not accurate enough to confirm anything: a person still checks every fact.

<BarChart data={queue_guess} x=model_guess y=rows title="Review queue by the model's guess" />

<BarChart data={queue_sport} x=sport y=rows title="Review queue by sport" swapXY=true />

The page reader reads a club's own page and proposes facts, each backed by a quote. Of {reader_sums[0].facts} facts in its pilot, {reader_sums[0].agree} matched what the data already said and {reader_sums[0].new_facts} were new for a person to check. The venue matcher, which decides when two records are one place, is tested against a hand-judged set:

<BigValue data={stats} value=gold_pairs title="Pairs in the gold set" />
<BigValue data={stats} value=gold_wrong_merges title="Wrong merges" />
<BigValue data={stats} value=gold_missed title="Missed matches" />

## Where the data is thin

Sports grouped by how well they are covered.

<BarChart data={status_counts} x=status y=sports title="Sports by coverage status" />

Some sports share one number because they are assumed to be playable on tennis courts. The map marks those as inferred. A venue that hosts several sports counts once for each, so the table does not add up to the venue total.

<DataTable data={coverage} rows=15 search=true>
  <Column id=sport />
  <Column id=venues fmt=num0 />
  <Column id=status />
</DataTable>

## How it is made

Built with Evidence.dev from the project's own checks. See [How it's built](https://abov.github.io/courtconnect-ca/how-its-built.html) and the [source code](https://github.com/abov/courtconnect-ca).
