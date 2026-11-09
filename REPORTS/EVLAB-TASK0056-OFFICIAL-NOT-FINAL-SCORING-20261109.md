# TASK0056 — 首场新云端前向比赛的官方赛果延迟与安全处理

**执行日期**：2026-11-09（北京时间）。**裁决**：实际赛后抓取、官方待确认状态分类与重试工程 **ACCEPT**；比赛2042640的独立盲评 **PENDING**，市场优势／正EV **NO EVIDENCE**。

## 1. 赛前来源不变

原始前向比赛ID：`2042640`。GitHub有效赛前冻结提交：`632aced51dabaee194c9a62ab58e3210bc8be3fc`；研究账本为`research/task0046_forward_20261108T071549Z_a336f71f27b5.json`。四个既定概率模型的输入不包含市场赔率或未来赛果。

源云端冻结`NEW_FORECAST_FREEZE.json` SHA256：

`a336f71f27b5f6117395a5ec80b76be29ccab3e9817583957c8b5c8330e28dcb`。

官方原定开球：2026-11-08 19:45 UTC（北京时间11月9日03:45），最早评分门槛：2026-11-08 22:45 UTC（北京时间06:45）。本轮09:03的实际检查已经超过最短三小时延迟，但**这不意味着比赛官方结果一定已完成或发布**。

## 2. 实际官方接口证据与第一次拒绝

2026-11-09 09:03:28北京时间，真实调用腾讯云`systemctl start evlab-task0054-cloud-score.service`，服务获取体彩官方`2026-11-09`比赛结果页，HTTP200并将原始字节和`SOURCE_MANIFEST.json`保存到不可覆盖的attempt目录：

`/home/ubuntu/evlab-forward-publisher-20261108/score-evidence/attempts/score-20261109T010332297690Z-42357b39/`。

源页出现目标比赛：

| 核验项 | 官方实际返回 |
|---|---|
| `matchId` | `2042640` |
| 主队 | 朗斯；`homeTeamId=179` |
| 客队 | 马赛；`awayTeamId=182` |
| `matchDate` | `2026-11-09` |
| `matchResultStatus` | **`1`（不是系统验收所需的`2`）** |
| 全场比分`sectionsNo999` | **空字符串** |

在原代码中，“官方不是最终状态”和“比赛身份冲突”合并为一个`ValueError`；实际服务退出2，保存`FAILED_RETAIN_ALL_EVIDENCE` journal：

`score-20261109T010332297690Z-42357b39.json`。

**这次没有评分，也没有编造比分。** 失败证据保留不删除，不能冒充成功。

## 3. 最小代码修正：保留严格身份门禁

改动`tools/task0044_forward_orchestrator.py`：

- 身份检查先于完赛状态；球队ID及官方比赛日期有冲突仍`ValueError`。
- 唯一可等待的状态是**同一比赛身份确认、状态为1、全场比分为空**，抛出专用`OfficialFinalPending`。
- 状态1但却有比分、其他未知状态、全场比分格式异常，仍为硬失败。

改动`tools/task0048_scheduled_score.py`：

- 捕捉`OfficialFinalPending`后，只有原始官方`SOURCE_MANIFEST.json`存在才写入`WAIT_OFFICIAL_FINAL`，同时保留结果根路径与等待理由；
- 不创建`BLIND_SCORE.json`和`INDEPENDENT_AUDIT.json`，不记入研究样本；
- 聚合结果为`WAITING_FOR_OFFICIAL_FINAL`，退出码0让每日任务继续保留而不是反复触发故障重试；
- 其他错误依旧`FAILED_RETAIN_ALL_EVIDENCE`且退出2，原独立验收与Git门禁均保持。

新增5个对抗性测试，全仓`527 passed`。本轮修复代码已提交并推送，提交`db66c4065af1c6d07f29dd095504b45535c86847`。

## 4. 真实自动重试及新结果

此前系统配置了`Restart=on-failure`、`RestartSec=300`。09:03失败后，**云端systemd在09:08:32自动重试**，从私有GitHub仓库`fetch/ff-only`至修复后的`db66c40`，并读取最新官方结果。

09:08:36，实际结果：

`{"task":"TASK0048","eligible_committed_cohorts":1,"status":"WAITING_FOR_OFFICIAL_FINAL","results":[{"status":"WAIT_OFFICIAL_FINAL","ledger_file":"task0046_forward_20261108T071549Z_a336f71f27b5.json"}]}`

新证据：

- create-only journal：`score-20261109T010836588508Z-92c786cc.json`，明确`WAIT_OFFICIAL_FINAL`，源根目录不覆盖首次失败；
- 官方HTTP原始结果页SHA256：`ec9fe6ce84b88513504d3f447f1ba62b8a682dec15ff687fb326a62a6818f3f8`；
- 新journal源原始freeze SHA仍为`a336f71f...`，匹配固定Git研究账本；
- `systemctl show`确认`Result=success`，`ExecMainStatus=0`，`NRestarts=1`；开始/结束INVOCATIONS完整配对。

一份独立只读现场验收检查了原冻结SHA、官方原始结果页SHA、官方主客球队ID/比赛日期、状态1/空比分、原始失败记录留存，并确认没有任何新`BLIND_SCORE`或`INDEPENDENT_AUDIT`。创建了不可覆盖证据：

`/home/ubuntu/evlab-forward-publisher-20261108/score-evidence/TASK0056_INDEPENDENT_RUNTIME_QA.json`

独立QA文件SHA256：`8cb36908c0b90d33a6f4100898972001ea0662245e394612e097145197f2b77d`；其判定`ACCEPT_RAW_RETAINED_CORRECT_OFFICIAL_PENDING`。

## 5. 下一真实检查点

腾讯云唯一发布者的11:15前向自动运行和11:40独立巡检（北京时间）尚未到期；18:30每日官方赛后评分和19:00巡检保持启用。下一次赛后官方状态如果仍不是最终状态，不计样本；如果取得`status=2`、完整全场比分、身份一致、独立QA通过，才算新的有效前向盲评。

**阶段裁决：解决了真实官方结果延迟导致运维误报和无谓重试的问题，研究数据完整性得到真实验收。模型有效性、PIT市场比较和正EV仍没有新证据。**
