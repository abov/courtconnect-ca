# 0030. Block the same-park merge for parks that hold separate facilities

Date: 2026-11-02. Status: accepted (owner, chat 2026-11-02; it changes a matching rule).

## Context
`int_court_pairs` links two courts when they are closer than `venue_radius_m` (75 m), and also when they sit inside the same named OSM park, school or club and are closer than `parent_merge_radius_m` (400 m). The second rule joins a school's courts that are a few hundred metres apart.

In San Diego the OSM park "Robb Field Ocean Beach Athletic Area" holds two facilities about 200 m apart: Barnes Tennis Center (private club) and the 12 public Robb Field tennis courts. The 400 m rule chained them into one cluster named Barnes Tennis Center. Result in the 2026-11-01 export: Barnes showed 39 tennis courts (about 27 are Barnes), the hand-added Peninsula Tennis Club venue was absorbed into it, and the only Peninsula pin was the Overture place 430 m away with 0 courts. Traced by loading the CI fixtures plus real OSM courts and park outlines for the area (2026-11-02).

## Decision
- New seed `parent_merge_block.csv` (`parent_name`, `evidence`, `verified_on`). For a listed parent (matched on the lower-cased name) `int_court_pairs` skips the same-parent 400 m rule; courts still join by the 75 m rule or `court_group_merge.csv`.
- One row today: Robb Field Ocean Beach Athletic Area. Rows need evidence that the courts are separate facilities (different operator or access, a gap, imagery); a person adds them, never an agent without owner approval.
- No change to `parent_merge_radius_m` and no change for any park not listed.

## Alternatives
- Lower `parent_merge_radius_m` (below about 200 m): one line, but it changes every park in the state and would split real single facilities; measure with `make eval-match` first.
- Only set the Barnes count with `venue_court_counts.csv`: fixes one number, leaves Robb Field without its own pin.
- A pair-level split seed (court id a, court id b): precise but needs many rows per park, since every Robb court pairs with every Barnes court.

## Consequences
- Barnes goes from 39 to 27 tennis courts; Peninsula Tennis Club gets its own venue at the courts (12 courts).
- Not fixed: the Overture Peninsula place stays as a second pin 430 m west with 0 courts (beyond the 350 m place-match radius). Needs its own decision.
- The gold-set eval (`make eval-match`) should be re-run after the next OSM refresh to confirm no change elsewhere; the seed has one row, so none is expected.
