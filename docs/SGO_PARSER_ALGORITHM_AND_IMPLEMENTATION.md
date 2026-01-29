### Context: SGO Arbitrage System — Algorithm, Parser, Logging, and Coverage

This document captures the end‑to‑end context of the recent work on the SGO integration: the redesigned arbitrage algorithm, parser architecture changes, logging/rate‑limit strategy, data quality validation, confidence scoring, and sport/market coverage. It also includes operational notes, security considerations, and next steps.


## Business Goals
- Show only real, actionable arbitrage opportunities (no false positives)
- Accurately compare bookmaker odds at the same line values (especially for player props)
- Keep logs useful while respecting Railway log limits
- Prepare for production launch with reliable data and clear UX


## High‑Level Data Flow
1) Fetch events and odds from SGO (Pro API): returns nested `byBookmaker` odds.
2) Normalize each odd via `oddID` structure: `statID-statEntityID-periodID-betTypeID-sideID`.
3) Build a unique market identifier per bookmaker‑specific line value: `stat_id + stat_entity_id + period_id + bet_type_id + line`.
4) Group odds by that identifier; track best odds per side across bookmakers.
5) Validate lines/bookmakers and filter suspicious data.
6) Compute arbitrage if total implied probability < 1.0.
7) Assign confidence score; emit opportunity objects to the frontend.


## Core Algorithm (Bullet‑Proof Version)
- Parse each SGO odd into components: `stat_id`, `stat_entity_id`, `period_id`, `bet_type_id`, `side_id`.
- Read bookmaker odds from `byBookmaker` and extract that bookmaker’s specific `overUnder`/line.
- Skip if the bookmaker has no usable line or invalid odds.
- Create `unique_market_id = f"{stat_id}_{stat_entity_id}_{period_id}_{bet_type_id}_{bookmaker_line}"`.
- Group by `unique_market_id`, then track per‑side best odds per bookmaker.
- Before arbitrage math:
  - Ensure at least two distinct bookmakers for the sides involved (no same‑bookmaker arb)
  - Ensure all sides’ best odds share the same numeric line
  - Reject suspicious bookmakers/placeholder data (e.g., Underdog +100 spam, `unknown`)
- Arbitrage calculation:
  - `total_implied_prob = sum(1 / decimal_odds)`
  - If `< 1.0`, arbitrage exists; compute profit: `((1 / total_implied_prob) - 1) * 100`.
- Confidence Scoring (simplified):
  - Factors: bookmaker quality mix, data freshness, line agreement, market type
  - Outputs: high/medium/low (numeric score stored alongside textual label)


## Parser Architecture: Key Changes
- Switched to bookmaker‑specific line handling: use each bookmaker’s `overUnder` from `byBookmaker` in the key.
- Fixed false positives by preventing cross‑line comparisons within a market.
- Introduced player name extraction applied consistently across football props (passing/rushing/receiving/kicking/defense/XP) and MLB props.
- Hardened the odd parsing for missing `stat_type` with safe fallbacks.
- Added start‑time and team name validation (filter out generic/malformed events).


## Market Identifier
We treat the market id as:
```
{stat_id}_{stat_entity_id}_{period_id}_{bet_type_id}_{line}
```
This ensures all odds grouped for comparison share the exact same line value and stat entity (e.g., player).


## Data Quality Validation
- Same‑bookmaker rejection: If both sides’ best prices come from the same bookmaker, skip.
- Line mismatch guard: If any best side line differs, skip market.
- Suspicious bookmaker/odd patterns:
  - Repeated +100 or known placeholder odds for fantasy books
  - `unknown` bookmaker id
  - Low‑confidence sources for specific props
- Event hygiene:
  - Valid start time and non‑generic teams (e.g., filter “Away” placeholders)


## Confidence Scoring (Multi‑Factor)
- Inputs: bookmaker quality, freshness, market type (main vs prop), line agreement, cross‑book dispersion
- Output: numeric [0..1] plus label (high/medium/low)
- High confidence requires strong, reputable books with fresh data and perfect line alignment


## Player Name Extraction
- For football: `passing_*`, `rushing_*`, `receiving_*`, `fieldGoals_*`, `extraPoints_kicksMade`, `defense_*` map to human names by parsing `stat_entity_id` (e.g., `LAMAR_JACKSON_1_NFL` → "Lamar Jackson").
- For MLB props: batting/pitching props convert to readable descriptions.
- Market descriptions:
  - `market_description`: concise (e.g., "Lamar Jackson Receiving Yards")
  - `detailed_market_description`: includes Over/Under framing when applicable


## Logging & Rate‑Limit Strategy
- Reduced noisy INFO logs to DEBUG (e.g., same‑bookmaker skips, large counts).
- Kept high‑signal INFO logs for created opportunities with full context.
- Minimized per‑market spam by sampling `byBookmaker` when debugging.
- Railway log health: fewer repeated messages, easier root‑cause tracing.


## Error Handling & Recent Fixes
- Fixed multiple `IndentationError` issues that previously prevented the service from importing and running.
- Guarded parsing steps with try/except where necessary; ensured early continues on malformed odds.
- Centralized checks to avoid partial state leaks and inconsistent groupings.


## Frontend Notes (Filters & UX)
- Bookmaker filter semantics: opportunity shown only if all participating bookmakers are selected.
- "Clear all" behavior corrected (no implicit re‑selecting from stored preferences).
- Independent min‑profit controls per tab (Arbitrage vs Live Odds), sane deletion behavior (no forced 0.1).
- Browser/local storage synchronization limited to intended tabs (no cross‑tab coupling required).


## Deployment & Operations
- Platform: Backend on Railway, Frontend on Vercel.
- Scheduler: extremely conservative intervals to preserve API quota.
- Email notifications: rate limits by subscription tier; immediate send on discovery.
- Observability: INFO for high‑signal, DEBUG for deep dives; reduced spam to avoid truncation.


## Security Review
- API key is never logged; loaded from environment.
- CORS restricted to known origins in production.
- HTTPS redirect and security middleware active in production.
- Input validation on query params (profit threshold, live_only).
- Avoids evaluating or concatenating untrusted inputs into queries; SQL handled via ORM.


## Current Sports/Markets Coverage
- Leagues: MLB, NFL/NCAAF, Soccer (moneyline/totals), Tennis (game totals), WNBA/CFL (main + some props)
- Player props: Receiving/Rushing/Passing (NFL/NCAAF), Kicking (FG, XP), Defense (tackles, sacks, interceptions), MLB batting/pitching props
- Main markets: Moneyline, Spread (sp), Totals (ou), Period variants where provided by SGO


## Known Limitations / Future Work
- MMA parser: implement full mapping of fight props and method of victory with line‑safe grouping.
- Expand basketball and hockey prop coverage with robust stat_id maps.
- Enhance confidence scoring with market depth and cross‑book consensus metrics.
- Add automated odds verification hooks (OddsChecker, direct book checks) for premium tiers.
- Batch fetch & caching for rate efficiency without staleness.


## Troubleshooting Playbook
- If “no opportunities”: verify service imports (no syntax errors) and SGO quotas; check INFO logs for market skips (line mismatch, same bookmaker).
- If “too many opportunities”: confirm unique_market_id includes line; ensure suspicious bookmaker filters are active; verify same‑bookmaker guard.
- If player names missing: inspect `_get_market_info` and `_extract_player_name` mappings for the relevant sport/prop.


## Summary of Key Implementation Edits
- Bookmaker‑specific line processing from `byBookmaker` with strict line alignment per market.
- Player name extraction across football props and MLB.
- Suspicious data/bookmaker filters to reduce fake arbs.
- Logging trimmed to avoid Railway truncation; preserve high‑value INFO logs.
- Multiple indentation/syntax fixes to ensure the SGO service loads and runs consistently.


## Next Steps
- Implement MMA parser end‑to‑end (fight, round, method, totals), matching the same market/line grouping rules.
- Add richer confidence scoring and market‑type specific thresholds.
- Instrument lightweight metrics (counts by sport/market, skip reasons) for continuous tuning.


