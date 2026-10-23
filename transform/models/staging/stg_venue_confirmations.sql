-- Individual confirmations of hand-added venues (transform/seeds/venue_confirmations.csv). One row per person, method and day.
select
    trim(venue_key)                              as venue_key,
    lower(trim(confirmed_by))                    as confirmed_by,     -- GitHub handle
    lower(trim(method))                          as method,           -- visited | official | reported (word of mouth)
    cast(nullif(trim(confirmed_on), '') as date) as confirmed_on,
    nullif(trim(evidence), '')                   as evidence
from {{ ref('venue_confirmations') }}
