---
title: CourtConnect data-quality scorecard
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

A snapshot of how complete and how fresh the CourtConnect data is, as of **{stats[0].as_of}**. Everything here is an aggregate count from the project's own checks; no venue rows are published. This is a prototype of a BI-as-code page, built with the open-source Evidence.dev from plain CSVs.

<BigValue data={stats} value=venues title="Venues on the map" fmt=num0 />
<BigValue data={stats} value=sports_with_venues title="Sports with a venue" />
<BigValue data={stats} value=sla_met title="Service levels met" />
<BigValue data={stats} value=gold_wrong_merges title="Wrong merges in the gold set" />

Of {stats[0].sports_total} sports on the master sheet, {stats[0].sports_with_venues} have at least one venue. {stats[0].sla_met} of {stats[0].sla_total} service levels are met; the miss is real (venue names, below).

## Trend, one point per refresh

History starts when the scorecard trend file starts, so the lines are short and will grow with each twice-monthly refresh.

<LineChart data={trend} x=date y=venues title="Venues on the map" yAxisTitle="Venues" />

<LineChart data={trend} x=date y=named_pct title="Venues with a real name (%)" yMin=0 yMax=30>
  <ReferenceLine y=25 label="Goal 25%" />
</LineChart>

Most OpenStreetMap courts are unnamed, so many pins carry a name inferred from the park or school. The map labels those as inferred; this chart is the share with a real name.

## Where the data is thin

Sports by coverage status. A status is the project's own label from `mart_sport_gaps`; the data dictionary and dbt docs describe the values.

<BarChart data={status_counts} x=status y=sports title="Sports by coverage status" />

Read the counts with care: several sports share one number (for example 8,090 for Frescotennis, Hand Tennis and Loboton) because they are inferred as also played on tennis courts. The map shows those as inferred, not as separate courts.

<DataTable data={coverage} rows=15 search=true>
  <Column id=sport />
  <Column id=venues fmt=num0 />
  <Column id=status />
</DataTable>

## How it is made

`make quality`, `make stats` and `make app-data` produce the numbers; `make dashboard-data` copies the aggregates into this project's CSV source. See [How it's built](https://abov.github.io/courtconnect-ca/how-its-built.html) and the [source code](https://github.com/abov/courtconnect-ca).
