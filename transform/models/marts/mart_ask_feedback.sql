-- Review list for the ask box: every question a visitor sent because it went unanswered, most-sent first.
-- Work it with `make ask-feedback`; when one is fixed (a new rule, data added, an answer written), log it in docs/feedback_log.csv.
select
    question_key,
    min(question)                        as question,
    sum(times_sent)                      as times_sent,
    count(distinct sent_on)              as days_sent,
    min(sent_on)                         as first_sent_on,
    max(sent_on)                         as last_sent_on
from {{ ref('stg_ask_feedback') }}
group by question_key
order by times_sent desc, last_sent_on desc
