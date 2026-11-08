# EV-Lab TASK0054｜云端唯一自动发布者与独立赛后评分切换

**现场切换日期**：2026-11-08，北京时间。  
**裁决**：**已验证的工程切换 ACCEPT；首次真正无人值守日报与首个新赛后盲评 PENDING。**

## 1. 源头和硬约束

上一阶段TASK0053在腾讯云影子环境得到未来比赛2042640的原官方数据、四模型概率，将不变原始冻结SHA通过Windows既有TASK0046严格Git发布程序锚定，远端提交`632aced51dabaee194c9a62ab58e3210bc8be3fc`，比赛开球`2026-11-08T19:45Z`（北京时间11月9日03:45）。该场已在TASK0048合格评分队列，最早可启动评分为北京时间11月9日06:45。

此前11月5/6/8 Windows前向计划任务出现`0xC000013A`，不等同成功采集或冻结；本轮**不删除原始故障记录**，只移交定时执行职责。

## 2. 云端私有Git最小权限实际验证

- GitHub仓库：`lixiuzuapple-a11y/football-betting-research`。2026-11-08专门创建的**单仓库**可写deploy key，GitHub登记ID`169157985`，不是个人GitHub登录Token；私钥只在云端私有目录`/home/ubuntu/evlab-cloud-git-auth-20261108/deploy_ed25519`且权限600。
- 云端独立仓：`/home/ubuntu/evlab-forward-publisher-20261108/git`，remote为该私有GitHub仓库的SSH URL，repo-local`core.sshCommand`明确使用该部署密钥。不使用先前老旧bundle当作生产事实源。
- 通过云端SSH实测GitHub`ls-remote`及完整私有`git clone/fetch`；临时分支`qa/task0054-cloud-auth-probe-20261108`实测push，远端SHA与本地相等，后再删除临时远端分支。**没有向GitHub提交任何密钥或访问令牌**。

## 3. 两项服务及自动触发真实证据

部署文件：

- `deploy/Run-Task0054-CloudForward.sh` 和`deploy/evlab-task0054-cloud-forward.service/.timer`：复用原`tools.task0046_forward_publication --mode publish`，在NTP同步、源数据/球队身份SHA、Git干净main、正确SSH远端、成功`fetch + ff-only`后才能运行；每日北京时间11:15。
- `deploy/Run-Task0054-CloudScore.sh` 和`deploy/evlab-task0054-cloud-score.service/.timer`：复用原`tools.task0048_scheduled_score`；每日北京时间18:30。
- 两者使用完全相同的`/home/ubuntu/evlab-forward-publisher-20261108/one-writer.lock`排他锁；日志另存非Git原始`evidence`及`score-evidence`。独立systemd非root用户`ubuntu`、`ProtectSystem=strict`和`NoNewPrivileges=yes`。
- 开启有界重试策略：`Restart=on-failure`，`RestartSec=300`，`StartLimitBurst=3`/`StartLimitIntervalSec=3600`，已从运行系统`systemctl show`回读验证。但**未进行人工注入故障后的自动重试实际验收**。

真实运行：

| 运行 | 北京时间 | 证据 |
|---|---|---|
| 云前向systemd服务人工启动 | 15:45 | 15:45:05→15:45:15，`STARTED/FINISHED`，exit 0 |
| 云评分systemd服务人工启动 | 15:48 | 15:48:50→15:48:55，exit 0 |
| 前向`systemd-run --on-active`时钟自动触发 | 15:49 | 15:49:53→15:50:04，exit 0 |
| 评分`systemd-run --on-active`时钟自动触发 | 15:50 | 15:50:21→15:50:25，exit 0 |

在首次云前向真实运行中，官方HTTP返回25场，1场满足模型身份，但正是已锚定的`2042640`；按原模型已提交ID去重门禁，正确返回`NO_NEW_ELIGIBLE_PREMATCH_FIXTURES`，**未重复提交**、未创建虚构新样本。云端原官方采集TASK0045持续健康。

将TASK0053原始云freeze SHA`a336f71f27b5f6117395a5ec80b76be29ccab3e9817583957c8b5c8330e28dcb`以create-only方式登记到云评分证据根，保留`manual_cross_host_relay`标记和原`probe`状态。原`anchored_candidate`复核真实Git提交`632aced`、比赛开球及源freeze，且新独立评分的两次服务运行均返回`WAIT_KICKOFF_PLUS_THREE_HOURS`，正确拒绝提前读取赛果。

## 4. 正式切换：唯一自动发布者

17:13:50，北京时间，执行腾讯云`systemctl enable --now`两个正式timer。

云端双重核验：

- `evlab-task0054-cloud-forward.timer`：`enabled`和`active`，下一次`2026-11-09 11:15:00 Asia/Shanghai`（03:15 UTC）。
- `evlab-task0054-cloud-score.timer`：`enabled`和`active`，下一次`2026-11-08 18:30:00 Asia/Shanghai`（10:30 UTC）。
- 当前Git源`c04c72d2601e0dce0cc896ff54d46204a7948c0e`（本次切换时的代码HEAD），干净且追平GitHub；云端TASK0045采集与health timer均为`active`，最新健康`status=OK`/SQLite`ok`。

**只有在上述两项timer真实生效之后**，17:14左右备份Windows原计划任务配置并停用，非删除：

| Windows旧任务 | 新状态 | 保存的XML原始SHA256 |
|---|---|---|
| `EVLab-TASK0046-DailyForward` | **Disabled** | `88d67ad22ea229b5de62d858b472429bf38a9d9ce2fb330ca244b71eb4d958b8` |
| `EVLab-TASK0048-DailyOfficialScore` | **Disabled** | `2b9d3826ff2737238a85196b8523ed6ab31e7a634f7eb7a4b62f5cfbfe0c2475` |

XML备份在`E:\WebCodex-Workspace\EVLab-Data-Backups\task0054-cloud-cutover-20261108\`；任务配置与历史运行日志均未删除。停用之后再次独立检查云两项timer都为`enabled/active`，Windows两个任务为`Disabled`。**现在只有云端的自动研究发布者处于启用状态**，Windows保留供回退时人工重启。

## 5. 测试与代码

定时器安全门禁测试文件：`tests/test_task0054_cloud_forward_deployment.py`，检查准确仓库remote、SHA、合法`--mode publish`、云端单写者锁、官方评分器、日历时区、禁用投注通道以及有界重试配置。

- 2026-11-08本轮全仓`509 passed`，`git diff --check`通过。
- 完成单仓库部署密钥真实写入／删除临时分支实测，系统服务实测、一次性真实日历触发、云端Git SHA比对、官方去重和早期评分拒绝。
- 初始云代码 `983bcd3`（前向）与`fc4659b`（评分）；后续配置提交`c04c72d`（有界重试）均已真实推送私有GitHub。最终验收报告以其后续报告提交为准。

## 6. 剩余不能提前宣称完成的部分

1. 第一次按**正式每日timer**在11月8日18:30进行评分运行、11月9日11:15正式自动前向运行，尚未实际发生。本轮只验证了同systemd服务的计时canary和正式timer启用/状态，需后续真实日志接受独立验收。
2. 新比赛`2042640`于11月9日03:45才开球，11月9日06:45后才有资格评分。首个计划中的云端评分日是11月9日18:30（北京时间），需届时确认官方完赛数据及赛后盲评，不能预报成绩。
3. 执行异常后的systemd故障自动重试未实际注入失败以验收；长期断网、服务器重启、认证密钥失效的处理仍需后续真实运行跟踪。
4. 本阶段是**研究链路运维交付，不是模型强于国际赔率**，没有投注、没有CLI盘口报价PIT、CLV或任何可复现正EV证据。

**综合裁决：基于真实服务、真实定时触发、两端唯一发布者切换和实际读回，TASK0054工程交付 ACCEPT；多日无人值守稳定性及首个新样本赛后评分 PENDING。**
