---
title: RacketConnect data-quality scorecard
---

```sql stats
select * exclude (as_of), strftime(cast(as_of as date), '%Y-%m-%d') as as_of
from courtconnect.stats
```

```sql trend
select cast(date as date) as date, venues, named_pct, tests_pass, sla_met, sla_total
from courtconnect.trend
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
select cast(date as date) as date, opened, closed, open_now from courtconnect.issues order by 1
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

How complete the RacketConnect data is. Counts only; no venue details are shown.

### The map, as of {stats[0].map_as_of}

<BigValue data={stats} value=map_venues title="Venues on the map" fmt=num0 />
<BigValue data={stats} value=map_sports_with_venues title="Sports with a venue" />

{stats[0].map_sports_with_venues} of {stats[0].map_sports_total} sports have a venue. These two numbers come straight from the map's data file.

### Quality checks, as of {stats[0].as_of}

<BigValue data={stats} value=sla_met title="Service levels met" />
<BigValue data={stats} value=gold_wrong_merges title="Wrong merges in the gold set" />

{stats[0].sla_met} of {stats[0].sla_total} service levels are met; the miss is venue names (below). These are re-measured at each refresh.

## Trend, one point per refresh

One point per refresh, so the lines are short for now.

<LineChart data={trend} x=date y=venues title="Venues on the map" yAxisTitle="Venues" />

<LineChart data={trend} x=date y=named_pct title="Venues with a real name (%)" yMin=0 yMax=30>
  <ReferenceLine y=25 label="Goal 25%" />
</LineChart>

Many courts are unnamed, so some pins use a name inferred from the park or school. This chart counts only real names.

## Feedback issues, open and closed

Reports sent through the map's forms, as GitHub issues. Updated daily.

<BigValue data={issue_totals} value=open_now title="Open now" />
<BigValue data={issue_totals} value=opened title="Opened, all time" />
<BigValue data={issue_totals} value=closed title="Closed, all time" />

<LineChart data={issues} x=date y=open_now title="Open issues over time" yAxisTitle="Open" />

<BarChart data={issues} x=date y={["opened","closed"]} title="Opened and closed per day" type=grouped />

## Site views over time

{view_totals[0].page_views} page views and {view_totals[0].events} clicks over {view_totals[0].days} days. Anonymous and approximate: ad blockers hide some visits.

<LineChart data={views} x=day y={["page_views","events"]} title="Page views and events per day" />

## Where the data is thin

Sports grouped by how well they are covered.

<BarChart data={status_counts} x=status y=sports title="Sports by coverage status" />

Some sports share one number because they are assumed to be playable on tennis courts. The map marks those as inferred.

<DataTable data={coverage} rows=15 search=true>
  <Column id=sport />
  <Column id=venues fmt=num0 />
  <Column id=status />
</DataTable>

## How it is made

Built with Evidence.dev from the project's own checks. See [How it's built](https://abov.github.io/courtconnect-ca/how-its-built.html) and the [source code](https://github.com/abov/courtconnect-ca).
