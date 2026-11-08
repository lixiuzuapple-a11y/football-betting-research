# EV-Lab TASK0053 — 云影子探针找到并正式冻结1场前向比赛

**日期**：2026-11-08，北京时间。  
**研究阶段裁决**：**云隔离探针与手动跨主机Git前向冻结 ACCEPT**；云端无人值守/直接向私有GitHub自动发布**NO-GO**；新冻结比赛赛后评分**PENDING**。

## 1. 已核实的基线事实

腾讯云TASK0045官方采集及健康检查11月8日持续`OK`，SQLite健康；约40 GB可用硬盘。腾讯云Ubuntu/Python可运行模型计算。

Windows TASK0046赛前定时在11月5、6日11:15及11月8日补跑时出现`0xC000013A`，有任务启动事件且缺少匹配FINISHED；先前电池许可和两次有界重试没有彻底修复。TASK0048赛后执行记录基本正常。**不能**再把Windows赛前调度列为可靠ACCEPT。

## 2. 严格隔离云验证与实际数据

云隔离目录`/home/ubuntu/evlab-forward-shadow-20261108/`，与长期运行的`evlab-task0045-official.service`分离；未修改现有systemd任务/服务、未启用新云端timer、未接触14/R9仓库。

- Git完整源代码归档：提交`c94270f2b9ee05fcb08da3207c921f5f666abb53`，源tar SHA256 `428cb839dfa24ae772bd62a7efbcfc3d3fa99149ac2357f04ff9c0557738a98d`。
- HF原始历史数据的冻结文件独立打包，tar.gz SHA256 `24153eb383a18f4ee37292264ea558a44a68e7d76d05f8d097ab919a07397a6a`；其中`fixtures.parquet`须满足原始清单的SHA，历史清单本体`eb3c37793866a27f8c1520c78a69e6098fdf79f08622b37fed64070fa1f8748f`。
- 已验收的球队身份JSON SHA256 `13d373dbab8363e606cfaf39c478b6035c35c86ad0ffcbf4c53e6e5014f63f2f`。
- 只在独立`venv`安装DuckDB `1.4.1`（与Windows验证环境一致），不触碰云端采集Python环境。

最初两次探针分别被**安全拒绝**，原因是将输出放在身份原始数据父目录下、缺少历史元信息文件。两次真实`FAILED_RETAIN_ALL_EVIDENCE` journal保留，并非隐去失败。修正目录隔离及补齐原始元信息后，第三次于`2026-11-08 07:14:16 UTC`成功：

- 官方源一次真实HTTP200，`26`场，原始JSON SHA256 `f13981a2489765dba9191e05a6ea7ef0476856856ac28f0d8ebfc60f483ee1e8`。
- 合格赛前预测**1场**：比赛ID`2042640`，开球`2026-11-08T19:45:00Z`（北京11月9日03:45），四个固定模型概率均产生。
- 云源冻结`NEW_FORECAST_FREEZE.json` SHA256 `a336f71f27b5f6117395a5ec80b76be29ccab3e9817583957c8b5c8330e28dcb`。
- 云上输出仍明确为`PROBE_LOCAL_UNANCHORED_NOT_ADMISSIBLE`，没有被擅自标记成正式Git冻结，也没有引入盘口或赛果。

## 3. 首次完成真正赛前Git锚（Windows严格门禁，未绕过）

将云上原始合格run完整打包并传至Windows非Git独立证据根：

`E:\WebCodex-Workspace\EVLab-Data-Backups\task0053-cloud-shadow-20261108\`

原始云run tar.gz SHA256 `f0f8c4b2cab7d568bee84df4a65cc64885afd63ced093f0d7395fc7e6e58a2b2`。Windows逐字节重验原源冻结SHA，与云端一致。

不重训练、不重新捕获、不改概率。通过原TASK0046：

1. `git_preflight`验证main干净、来源remote为正确私有仓库、fetch origin/main与本地一致；
2. `build_ledger`核对原冻结时间距当前小于30分钟、原始官方来源SHA、球队身份、四模型、尚未提交比赛ID、至少提前60分钟；
3. `publish`写create-only记录`research/task0046_forward_20261108T071549Z_a336f71f27b5.json`，Git提交、push且远端HEAD完全一致；
4. `verified_freeze`再次验证源文件SHA和Git提交中的概率逐项一致。

**实际远端提交**：`632aced51dabaee194c9a62ab58e3210bc8be3fc`，验证时间`2026-11-08 07:15:55 UTC`（北京时间15:15:55），距本场开球约12小时29分钟；赛事尚未开始。Git里的账本SHA256为`354cf7cd345d703b7a3a9c75c54231d6ad39f3feefafafe9d76ec987ded8f6ff`。

注意：这是**一次人工触发的云probe→Windows正式Git发布**，不能冒充腾讯云服务自己已无人值守发布。

## 4. 实际接入赛后独立评分，不在开球前偷窥赛果

为使现有TASK0048评分器自动发现这场新比赛，利用create-only方式把**相同SHA的云源原始run**登记到原Windows批准的`task0046-forward-20261031/runs`及`journal`。保留单独的`manual_cross_host_relay=true`和最初云probe非正式状态，而不是修改、删除云端原始journal。

新登记journal SHA256：`c9fd2b14a6122e810e702ac70e7ef373d0303b024f31c88339a193a4ab8e7247`；原`anchored_candidate`实际核验Git blob、远端祖先、本地源冻结SHA、原始Git提交早于开球，结果`match_count=1`、`due_now=false`。

进一步**实际运行TASK0048评分主程序**：`2026-11-08 07:18:09 UTC`，识别到`eligible_committed_cohorts=1`并返回`WAIT_KICKOFF_PLUS_THREE_HOURS`，留真实create-only评分journal。这是正确的拒绝提前赛后评分，而非任务失败。

本场最早允许评分：`2026-11-08 22:45 UTC`（北京11月9日06:45）。原Windows每日18:30评分任务可能在11月9日进行，但还没有真实到期执行的证据，必须等实际官方赛果与独立QA完成才能记为已评分。

## 5. 还没有解决的工程与科学闸门

1. **云端正式自动发布NO-GO**：云主机既有Git源`/home/ubuntu/t0005.bundle`版本滞后，无当前私有GitHub可写authenticated remote；不能在云上省略Git远端锚定。没有启用定时发布或获取新密钥，也不修改现有生产采集。
2. **Windows任务可靠性REJECTED**：先前`0xC000013A`仍未根因消除。此次发布用前台WebCodex执行而非11:15计划任务。
3. **前向新样本N=1且未开奖**：此刻没有Log Loss/Brier成绩；原历史研究与国际市场赔率同时间PIT结论仍为NO-GO。新样本不能说明模型盈利，更不能下注。
4. **研究单一性**：本任务完全没有涉及14/R9，亦未安装投注机器人。

## 6. 阶段研究价值

从此前“本地任务漏跑、前向N=2停滞”推进到真实官方26场→严格门槛1场→云端成功概率冻结→原Git发布门禁提前12小时推送→官方赛后队列真实识别未到期。这个**跨主机完整链路的单次实证**是真正增量。

下一阶段若投入云无人值守，需要在**有限权限**下完成私有Git安全凭据、唯一发布者锁、断线/双主机冲突处理、时间来源与自动健康告警，然后再逐日验收；没有这些不能停止原链路或声称完成迁移。
