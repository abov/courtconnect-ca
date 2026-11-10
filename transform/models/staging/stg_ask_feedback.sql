-- Questions visitors chose to send from the ask box ("Send this question to us"), one row per day and question.
-- Source: ingestion/extract_ask_feedback.py (from the GoatCounter export). Text is already scrubbed of emails, links and phone-like numbers.
-- Local warehouse only: never export this to the repo, the app or the dashboard (the repo is public).
select
    cast("day" as date)                  as sent_on,
    trim("question")                     as question,
    trim(lower(regexp_replace("question", '[^a-zA-Z0-9]+', ' ', 'g'))) as question_key,
    cast("count" as integer)             as times_sent
from {{ source('raw', 'ask_feedback') }}
where "question" is not null and trim("question") <> ''
