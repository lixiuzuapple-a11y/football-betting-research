# Local workspace layout

## Canonical Windows workspace

As of 2026-09-29, the local Windows checkout for this repository is:

`E:\OneDrive\OneDrive - Swire Properties Limited\webcodex\football-betting-research`

The parent directory:

`E:\OneDrive\OneDrive - Swire Properties Limited\webcodex`

is now only a workspace container and is **not** itself the Git repository.

Expected sibling layout:

```text
webcodex\
├─ football-betting-research\   # EV-Lab / this repository
└─ li-iptv\                     # future independent IPTV repository
```

Each project must keep its own independent `.git` directory. Do not nest one Git repository inside another repository.

## WorkBuddy / Executor handoff

Before doing any further EV-Lab work on the Owner Windows machine:

```powershell
cd "E:\OneDrive\OneDrive - Swire Properties Limited\webcodex\football-betting-research"
git status -sb
git remote -v
```

Expected remote:

`https://github.com/lixiuzuapple-a11y/football-betting-research.git`

Do not run EV-Lab Git commands from the parent `webcodex` directory.

This local-path relocation does **not** change the cloud TASK-0006 sealed run. The cloud collector remains pinned to its frozen cloud checkout/commit and must continue under the existing TASK-0006 rules.
