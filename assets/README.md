# Reusable identity assets

## team_name_map.json

Canonical deployable copy promoted from the Owner history bundle for TASK-0007.

- source: `history/_review/18_data_其他派生素材/data/team_name_map.json`
- source SHA-256 at promotion: `2816D72BE53A55292AEA4009C76F7DBD35CF9DFA01819C0B6CED96A90597F307`
- purpose: conservative Chinese Sporttery team name ↔ English market identity matching
- provenance: legacy EV-Lab team-name mapping asset; includes league-grouped `en`, `cn`, `cn_full`, aliases and per-entry source notes where present

The history bundle is intentionally ignored by Git, so this tracked copy exists to make the reusable identity layer deployable and reproducible. Future identity-only additions should be reviewed, versioned here, and must not be inferred from odds or research outcomes.

### TASK-0007 identity-only supplement

On 2026-10-08, 38 Chinese-English identities from 19 current fixtures were added under `TASK0007_IDENTITY_ONLY`. Each pair was admitted only when the full captured Sporttery and BetExplorer fixture universes contained the same home/away identity with the same kickoff. Odds, price changes, EV, outcomes and D01-B candidate status were not consulted. The entries retain the matched provider IDs in `_verified_fixture` for audit.

Fixtures with no corresponding BetExplorer identity record (for example the captured Australia-Brazil and Japanese League Cup rows) were deliberately left unmatched rather than inferred.
