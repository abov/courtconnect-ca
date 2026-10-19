# Imagery sweep pilot: Sherman Oaks / Van Nuys / Encino / Tarzana / Studio City (2026-10-18)

**Question:** can a cheap aerial-imagery pass find courts and walls that OSM, Overture and city pages miss (the owner found the Van Nuys Sherman Oaks Park wall and pop tennis courts on Google Maps by hand)?

**Method:** 134 venues in lat 34.12-34.22, lon -118.56 to -118.36; kept named venues or 3+ court venues, merged points within 40 m: 44 views. Esri World Imagery z19 (about 0.3 m/pixel, 108 x 84 m per view, viewing only, nothing stored), a yellow 20 x 34 ft reference box in each view, 6 views per contact sheet (8 sheets), then z20 close-ups for 3 spots. Cost: one script run (about 400 tile requests) plus 9 image reads.

**Results**
- Painted court floors are easy to see: the 8 tennis courts + 2 paddle-size courts + wall court at Van Nuys Sherman Oaks Park, the 4-court block at Lake Balboa, the lined 3-court block at an unnamed Van Nuys complex.
- Walls are not: a 16 ft wall is a 1-2 pixel line plus a shadow. The only wall found from above was the one with a painted floor (VNSO). No further unmapped painted wall courts in the 44 views.
- Candidate for a visit/photo (not added): **Teichman Family Magnolia Park, Van Nuys** (34.1659, -118.4689). OSM lists 2 Tennis courts, but at z20 each is about 8.7 x 18.6 m (28 x 61 ft), smaller than a 36 x 78 ft tennis court and equal to the 60 x 27 ft court in our sheet for Pop Tennis (also a 3/4-size junior court). The LA Parks page for the park was not found; needs a city page or a photo.
- Checked, consistent with the map: Lake Balboa (4 OSM handball floors on a lined asphalt block), Van Nuys Recreation Center (handball paving next to the 2 tennis courts; the city page lists "Handball Courts (Lighted)").
- Not locatable from above: the large green wall at Balboa Sports Center (owner photo): the gym, ball fields, tennis courts and a lined paved court are visible, but the wall's spot is not. Added as an approximate `reported` pin at the venue centre.
- 5 of the first 12 views were private backyard courts: skip pins that are home-like.

**Recommendation for scaling**
1. Do not run a blanket aerial sweep for walls: low yield, and the wall itself is invisible. A painted-floor detector (20 x 34 ft and 20 x 50 ft rectangles near known courts) could flag small courts, but only after the beta.
2. Highest-yield and cheapest: the owner's Google Maps sightings (screenshot -> measure on Esri -> seed row) worked three times in one session; make it a standing route (a "Sightings" step in the runbook, `reported` rows with the imagery size test).
3. Text lists: LA Parks facility pages list "Handball Courts" and "Paddle Tennis"; scrape per-park feature lists city by city (public pages), starting with LA.
4. Send corrections upstream: the owner can add the walls and small courts to OSM (ADR 0011 edit link) so every consumer gets them.
