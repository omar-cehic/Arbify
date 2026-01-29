### SGO Arbitrage Parser — Football & Soccer Comprehensive Status and Debug Plan

This document summarizes what has been implemented, our bullet‑proof arbitrage algorithm, current findings from Railway logs, why football/soccer arbs may be sparse, and the active debug plan. Use this as context for future work or new chats.

## What’s Implemented (High-Level)
- Parser aligned to our algorithm with bookmaker‑specific lines and strict same‑line comparison.
- Comprehensive market recognition for Baseball, Football, Soccer with period support.
- Human‑readable `market_description` and `detailed_market_description` surfaced to frontend and emails.
- Email filtering logic aligned with frontend filters (min profit, bookmaker selection).
- Calculator bookmaker matching fixed (robust name matching) and odds displayed in American format.
- Logging tuned to avoid spam; targeted debug logs added for football/soccer.
- Scheduler cadence increased to reduce staleness while respecting plan quota.

## Core Algorithm (Authoritative)
- Parse each SGO odd into: `stat_id`, `stat_entity_id`, `period_id`, `bet_type_id`, `side_id` (from `oddID`).
- Read odds per bookmaker from `byBookmaker`; extract that bookmaker’s `overUnder` (line) when present.
- Skip odds with missing/invalid data.
- Build unique key: `{stat_id}_{stat_entity_id}_{period_id}_{bet_type_id}_{line}` (line omitted only for no‑line markets like ML).
- Group by this key; track best odds per side across distinct bookmakers.
- Guards before arb math:
  - At least two distinct bookmakers across the sides
  - All best sides share the exact same numeric line
  - Filter suspicious/placeholder books (e.g., `unknown`, +100 spam)
- Arb calculation: `sum(1/decimal_odds) < 1` → arbitrage; profit = `((1/sum) - 1) * 100`.
- Filter out ~0% profit; compute confidence (book mix, freshness, line agreement, market type).

Reference: `docs/SGO_PARSER_ALGORITHM_AND_IMPLEMENTATION.md`

## SGO Docs Coverage (Reference)
- Football (market list and identifiers): https://sportsgameodds.com/docs/data-types/markets/football
- Soccer (market list and identifiers): https://sportsgameodds.com/docs/data-types/markets/soccer

## Football Coverage (Implemented)
- Main markets: Moneyline (game/reg/halves/quarters), Spread (game/reg/halves/quarters), Totals (game/reg/halves/quarters), Even/Odd, Yes/No.
- Player props (with period support where available):
  - Passing: yards, touchdowns, completions, attempts, interceptions, longest, rating, sacked
  - Rushing: yards, touchdowns, attempts, longest
  - Receiving: yards, touchdowns, receptions, targets, longest
  - Defense: interceptions, sacks, tackles (solo/assisted/combined/total), forced/recovered fumbles, passes defended, QB hits, TFL, safeties
  - Kicking: field goals made/attempted/longest, extra points made/attempted, kicking total points
  - Returns: kick/punt returns yards/attempts/longest/touchdowns
  - Specials: anytime/first/last touchdown, fantasy score
  - Combined stats: `passing+rushing_yards`, `rushing+receiving_yards`, `touchdowns`
- Period support: `1h`, `2h`, `1q`, `2q`, `3q`, `4q`, `reg`.
- 3‑way ML where applicable.

## Soccer Coverage (Implemented)
- Main markets: Moneyline (game/reg/1H), Spread, Totals (game/reg/1H), Even/Odd, Yes/No, Both Teams To Score, 3‑way ML and compound sides (`home+draw`, `away+draw`, `not_draw`).
- Player/team props (with period support where applicable):
  - Scoring: goals (player/game/team), anytime goals (YN), even/odd
  - Shooting: shots, shots on target (`shotsOnTarget`/variants), shots off target, shot attempts
  - Passing: assists, passes (attempted/completed/successful/accurate), key passes, crosses (completed), long/through balls
  - Dribbling: dribbles, dribbles attempted/completed
  - Defensive: tackles, interceptions, blocks, clearances, fouls, fouls drawn/committed
  - Cards: yellow, red, combined, weighted (team/player variants)
  - Keeper: `goalie_saves`, `goalie_goalsAgainst`; (plus `saves`, `punches`, `catches`, `clean_sheets` variants)
  - Other: minutes played, offsides, duels won/lost, aerial/ground duels, possession/touches, possession lost, dispossessed, errors, big chances created
- Period support: `1h`, `2h`, `reg`.

## What Logs Show Right Now
- Football: opportunities exist (e.g., Oregon State vs Houston ~2.21% profit; hundreds of markets processed).
- Baseball: steady arbitrage opportunities.
- Soccer: events identified as SOCCER, but opportunities often 0.

## Why Football/Soccer Arbs May Be Sparse
- Line fragmentation: strict same‑line rule (e.g., soccer totals 2.25/2.5/2.75) reduces cross‑book matches.
- Bookmaker symmetry: enough books on one side, not enough on the opposite side at the same line.
- Same‑bookmaker guard: same book best on both sides → correctly rejected.
- Freshness: mismatched update times across books → markets skipped by freshness/quality checks.
- Market recognition edge cases: select soccer basic markets may not always map to intended market_type in rare league/oddID variants.

## Active Debugging (Deployed)
- Added soccer‑focused logs:
  - `SOCCER PROCESSING: <home> vs <away> - <count> markets`
  - `BASIC SOCCER:` logs for `points-home-game-ml-home`, `points-away-game-ml-away`, `points-all-game-ou-<side>` recognition and mapping
  - Expanded target teams (e.g., Juventude, Vasco, Bahia, Internacional, Brentford, Man Utd) for visibility
- Moneyline grouping fixed (no `_None` line id); strict same‑line totals preserved (no cross‑line normalization).

## Next Remediation Steps (Based on New Logs)
- If basic soccer ML/totals not recognized: adjust `_get_market_info` `points`→`ml/sp/ou` mapping for soccer to ensure correct `market_type`, `side_id`, and grouping key.
- If recognition is fine but no arbs: analyze bookmaker overlap and freshness; consider confidence tuning or investigative logging of per‑line book counts.
- Verify all `ml3way` compound sides always map to market_types.

## File of Interest
- Main service: `backend/src/services/sgo_pro_live_service.py`

## Appendix — Guardrails We Will Not Relax
- No cross‑line arbitrage (e.g., totals 2.5 vs 2.75 are not comparable).
- No same‑bookmaker arbitrage.
- Exclude suspicious/placeholder books and stale data.

## References
- Algorithm and architecture: `docs/SGO_PARSER_ALGORITHM_AND_IMPLEMENTATION.md`
- Football markets: https://sportsgameodds.com/docs/data-types/markets/football
- Soccer markets: https://sportsgameodds.com/docs/data-types/markets/soccer


