# D01-B lead-lag external method scout — 2026-10-08

## Purpose

A narrow external-world check before opening TASK-0006 event-level results. This does not replace the project''s existing Edge Space work and does not inspect the prospective dataset.

## Relevant external evidence

1. **Croxson & Reade — "Exchange vs. Dealers: A High-Frequency Analysis of In-Play Betting Prices" (2010 working paper).**
   High-frequency matched exchange/bookmaker data are used to study price discovery; the reported direction supports exchange-led information aggregation in that setting.

2. **Flepp et al. / fast trading evidence — "The effect of fast trading on price discovery and efficiency: Evidence from a betting exchange" (Journal of Economic Behavior & Organization, 2018).**
   Uses event-study timing windows around material sports information and shows that faster-informed traders can account for much of short-run price reaction. Methodological relevance here is the explicit treatment of time ordering and latency windows, not the live-tennis result itself.

3. **Franck, Verbeek & Nüesch — "Prediction accuracy of different market structures — bookmakers versus a betting exchange" (International Journal of Forecasting, 2010).**
   Football evidence finds betting-exchange prices more predictive than traditional bookmaker prices in the studied sample.

4. **Flepp, Nüesch & Franck — "The liquidity advantage of the quote-driven market: Evidence from the betting industry" (Quarterly Review of Economics and Finance, 2017).**
   Matched bookmaker/exchange football odds show that market-structure/liquidity conditions can alter relative pricing. This cautions against assuming one venue is always the superior price.

## What this changes for TASK-0007

It supports the **method family**:
- matched contracts;
- timestamped observations;
- lead-lag / event-window analysis;
- explicit market-structure caveats.

It does **not** support upgrading BetExplorer into a named sharp feed.

TASK-0007 therefore keeps the source label `reference_proxy`, treats post-move probability as a proxy-implied benchmark only, and requires a future stronger replication before any positive-EV claim.
