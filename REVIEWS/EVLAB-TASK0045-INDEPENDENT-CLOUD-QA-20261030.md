# TASK0045 independent QA — continuous EV-Lab cloud capture (2026-10-30)

Reviewer: ChatGPT, direct cloud status/SQLite/raw/journal inspection, independent
source SHA/byte audits, simulated process faults, complete offcloud artifact
restore. These checks are independent from a sole executor's self-report.

| Gate | Evidence | Verdict |
| --- | --- | --- |
| Historical failure cause | old unit still failed exit 2, normal no-offer incorrectly counted as empty, Restart=no | ROOT CAUSE CONFIRMED |
| Correct collector code deployed | repo/cloud exact SHA256 7abec388...e9842b5fd | ACCEPT |
| Persistent service installed | enabled and active, PID, Restart=always, 30sec cooldown, bounded unique roots | ACCEPT |
| Watchdog installed | timer enabled+active, scheduled every 2min, full SQLite and all raw SHA / stale/disk checks | ACCEPT |
| Live official source | first epoch two real HTTP200, independent raw SHA 2/2 | ACCEPT |
| Monitor self-recovery | real SIGKILL and watchdog ALERT/restart at 15:36:12, then health OK | ACCEPT |
| Pure systemd crash recovery | watchdog disabled temporarily, SIGKILL, systemd Scheduled restart job 15:39:37, NRestarts=1, new root | ACCEPT |
| Non-destructive archives | 3 pre-15:41 epoch roots 2+3+2 captures, full 7/7 raw SHA, SQLite checks all pass | ACCEPT |
| Successful rollover | isolated real two-epoch run; two CYCLE_OUTCOME exit0 and 1/1 source SHA each | ACCEPT |
| Off-host restore | copied two stopped epochs to E drive; hashes independently replayed | ACCEPT |
| No-offer handling | corrected classifier and previous TASK0041 real 11 no_offer events; 11 targeted tests with synthetic no-offer | ACCEPT classifier, not this live window |
| Monitor error classification | latest single transport error is DEGRADED, 3 consecutive = ALERT; 11 focused tests and monitor SHA reverified cloud | ACCEPT |
| Full regression suite | 430 passed, no unrelated repo changes | ACCEPT |
| Reboot and long-run endurance | systemd enabled, but server not actually rebooted, no 48h/7d elapsed | PENDING |
| External alert and autonomous offsite backups | local health journald+JSON only; manual off-cloud recovery demonstrated | NOT IMPLEMENTED |
| EV / ROI / CLV / bets | no model or execution touched | OUT OF SCOPE |

**Engineering decision: TASK0045 ACCEPT for deployed continuously running
cloud data collector with real observed auto-recovery and integrity checks.**
It is not an acceptance of indefinite guaranteed uptime or economics. Do not
turn off the fixed new service in order to run more demonstrations; future
audits should be read-only unless genuine malfunction occurs.
