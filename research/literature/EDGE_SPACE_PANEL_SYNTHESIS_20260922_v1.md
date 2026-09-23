# EDGE SPACE 外部 AI 联合审阅与最终合并 v1.0

**项目**：中国体育彩票竞彩足球长期正期望收益研究
**日期**：2026-09-22
**性质**：外部 AI panel review + 第一原理裁决 + 旧研究证据交叉核对
**状态**：FRAMEWORK SYNTHESIS COMPLETE / READY FOR LEGACY-EVIDENCE MAPPING

---

## 0. 本轮输入与边界

本轮共审阅 6 份独立 Edge Space Enumeration 输出，另有 1 份外部 AI 提示词文件。提示词不参与“投票”。

| ID | 文件 | 报告自报根数 | 自报二级机制 | 自报策略族 |
|---|---|---:|---:|---:|
| EAI-01 | `AI_EDGE_SPACE_REPORT_01_FULL.md` | 4 | 12 | 20 |
| EAI-02 | `竞彩足球正EV路线空间穷举_Edge_Space_Enumeration.md` | 5 | ≈18 | ≈25–30 |
| EAI-03 | `竞彩足球正EV路线穷举.md` | 7 | 18 | 22 |
| EAI-04 | `AI_EDGE_SPACE_REPORT_04.md` | 5 | 14 | 14 |
| EAI-05 | `AI_EDGE_SPACE_REPORT_05.md` | 6 | 28 | 33 |
| EAI-06 | `edge-space-enumeration-report-v1.md` | 5 | 27 | 12 |

另：
- `prompt-v2-external-AI.md`：提示词，不计入 panel 输出。
- 旧研究交叉核对来源：
  - `结案报告_竞彩足球长期正收益_v1.md`
  - `研究方法论_可迁移框架_v2.md`
  - `INVENTORY-20260921-01_竞彩足球研究资产只读盘点(2).md`

---

## 1. 先纠正所有报告共享或重复出现的事实风险

### 1.1 当前竞彩返奖奖金比例不是 73%，而是 70%

官方时间线：

- 2009：69%
- 2014-10：73%
- 2019-02-11：71%
- 2020-11-01：70%
- 国家体育总局体育彩票管理中心 2026 年公开材料明确写明：70% “并延用至今”。

因此，所有把“当前竞彩=73%”作为基准的外部报告，其当前制度前提均错误。

### 1.2 2014 年规则页面长期在线，不代表仍然有效

中国竞彩网仍能检索到写着：
- 72% 当期奖金 + 1% 调节基金；
- 73% 返奖；
的 2014 历史规则页面。

但 2019 规则已明确取消原 1% 调节基金，返奖由 73% 调至 71%；2020 再调至 70%。

因此：
> **规则页面必须按 effective date/version 处理，不能“搜索到一页规则就当当前规则”。**

### 1.3 “制度返奖比例 70%”不能直接变成“单场 overround = 42.9% hurdle”

这是本轮最重要的纠错。

对某一场具体市场，真正的价格门槛来自实际可执行赔率：

`p_break_even = 1 / O_exec`

如果将该市场各选项的倒数赔率和记作：

`S = Σ 1/O_i`

则在 proportional no-vig 参考下：

`q_i = (1/O_i)/S`

正 EV 条件为：

`p_i > S q_i`

需要的相对概率 uplift 是：

`p_i/q_i - 1 > S - 1`

也就是说：
> **真实 hurdle 是该场、该玩法、该时点的 quote geometry / overround，而不是把全国游戏资金分配比例机械倒数。**

旧研究《结案报告》本身已经记录过这一纠错：
- 初版曾用“70% ⇒ 42.9% 门槛”；
- 后续实测后推翻；
- 不同玩法的实际 quote overround 明显不同。

旧资产里曾记录的历史实测值包括：
- had ~12.9%
- ttg ~17–24%（按时期变化）
- crs 更高
但这些数值仍需要按新 QA 标准复核，不能直接视为当前真值。

### 1.4 当前确定的执行规则

官方当前/有效材料支持：

- 固定奖金在销售过程中可根据投注额和其他因素调整；
- **完成投注时的固定奖金锁定**，后续变化不影响已出票；
- **同一场比赛不同游戏不能混合过关**；
- 无效场次：单场退票；过关去掉该场后按原投注时刻相应固定奖金重算；
- 2020 新规：单票购买金额不超过 6000 元；
- 单人单日累计超过 1 万元（不含）需预约实名登记；
- 单台终端还有日销售限额；
- 某些过关场数对应最高奖金限额。

这意味着：
> 任何 stale-price、相关腿、同场跨玩法、容量策略都必须通过真实 execution adapter，不能只做数学赔率比较。

---

## 2. 外部 AI 的“数量”不能投票决定

六份输出得到：

`N_root = 4, 5, 7, 5, 6, 5`

表面中位数约为 5，但这不是我们采用 5 根的理由。

更严重的是，多份报告内部计数并不一致：

### EAI-01
声称 12 个二级机制，但树状结构按其自身层级实际并不等于 12。

### EAI-03
声称：
`N_sub = 18`
但根树逐项按 SUB 数量为：

- R1 = 4
- R2 = 2
- R3 = 3
- R4 = 3
- R5 = 4
- R6 = 3
- R7 = 3

总计 = 22，而不是 18。

### EAI-04
声称：
`N_sub = 14`
但树上 5 根 × 每根 3 个 SUB，实际 = 15。

结论：

> **“策略共有 20 / 22 / 33 条”不是数学事实，而是拆分粒度的产物。**

只有先冻结：
- 什么叫 root；
- 什么叫 sub-mechanism；
- 什么叫 strategy family；
才能谈数量。

---

## 3. 为什么各 AI 会得到 4 / 5 / 6 / 7 根

真正分歧只有四个边界。

### 3.1 Conditional / Segmentation 是否是根？

裁决：

`NO`

理由：

条件选择：

`E[EV | X∈A]`

只有当 A 内存在：
- 信息差；
- 定价差；
- 合同结构差；
- 时序差；
- 外部转移；
之一时才会产生正 EV。

“只选某联赛 / 某赔率区间 / 某球队 / 某时间段”本身没有改变任何 EV 原语。

因此：

`Conditional / Segmentation = OVERLAY / SEARCH AXIS`

不是 root。

这是 EAI-03（7 根版）的主要结构性错误，也是外部 panel 对我们原 v2.9 六根框架最有价值的纠偏。

### 3.2 Cross-market arbitrage 是否是独立根？

裁决：

`NO`

跨市场套利的 payoff 来自：
- 不同 venue 的报价差；
- 多合同组合；
- 执行/访问条件。

它是：
`Pricing × Contract × Execution`
的复合策略。

“跨市场”描述的是 action set / venue，不是新的 EV 物理来源。

因此不单列 root。

### 3.3 Timing / Execution 是否是根？

严格代数层面：

`NO`

时间本身不创造价值。

Timing 只有通过：
- 获得新的信息集；
- 访问旧/新报价；
- 改变可执行 action set；
才影响 EV。

但工程研究层面：

`YES, KEEP AS APPLIED ROOT`

理由：
- 需要完全不同的数据（高频 quote + event timestamp）；
- 证伪方法不同（lead-lag/event study/latency window）；
- 它是目前多个 AI 共同指出的剩余关键路线；
- 若完全吞进 Information/Pricing，会隐藏最重要的工程问题。

因此我们区分：

- **Algebraic primitive**：Timing 不是独立原语；
- **Applied research root**：Timing/Execution 保留。

### 3.4 Information 与 Market Pricing 是否应该合并？

裁决：

`SEPARATE AT APPLIED ROOT`

虽然最终都是围绕 `p` 与 quote 的关系，但研究问题不同：

Information：
> 我们能否比市场更准确地推断状态概率？

Pricing：
> 即使没有新的比赛信息，竞彩的 quote 是否由于需求、产品、竞争/机制而系统性偏离 reference fair price？

两者的数据、失败方式、稳定性不同。

但 Information 内部应再区分：

- information-set advantage（知道更多/更早）
- inference advantage（同样信息推断更好）

这采纳 EAI-06 的一个重要观点。

---

## 4. 最终两层分类：解决“到底几根”的争论

### 4.1 Level-0：数学原语层

对一个可执行 action `a`：

`EV(a,t) = Σ_s P(s | F_t) * R_s(a,t) + B(a,t) - Cost(a,t)`

最小代数层只有三类价值来源：

#### P0-A — Probability / Belief
改变对 `P(s|F_t)` 的有效认识。

#### P0-B — State-contingent Payoff
获得不同的 `R_s(a,t)`：
- quote
- contract
- multi-leg payoff
- settlement

#### P0-C — External Transfer
合同之外的 `B(a,t)`：
- bonus
- rebate
- subsidy
- mechanical payout

另外有一个不是 edge、但决定 edge 能否实现的：

#### P0-X — Feasible Action Set
`A_t`
包括：
- 时间
- venue
- 单关/串关可得性
- cutoff
- cap
- limit
- execution latency

因此：

> 如果只问“代数上正 EV 从哪来”，答案接近 3 个 primitive + 1 个 feasibility dimension。

这解释了为什么 4-root 报告并非完全错误。

---

### 4.2 Level-1：本项目 Applied Research Roots

为了研究和实验，我们冻结为 **5 根**：

## R1 — Information / Inference Edge
信息或推断使 `p̂` 更接近真实概率。

## R2 — Pricing / Market Microstructure Edge
竞彩 quote 相对 fair/reference price 存在系统性残差。

## R3 — Product / Contract Edge
状态 payoff、M串N、联合分布、结算规则产生非线性失真。

## R4 — Timing / Access / Execution Edge
因信息/报价传播延迟而在某个窗口获得不同的可执行状态。

## R5 — External / Mechanical Edge
正常合同之外的 subsidy / error / settlement anomaly 等价值转移。

### 不再作为 root 的东西

- Conditional / Segmentation → overlay
- Cross-market arbitrage → composite strategy
- Model family → implementation
- Kelly / sizing → downstream capital allocation
- CLV → diagnostic metric
- Automation/UI → execution infrastructure
- Capacity → viability constraint
- Reference market → measurement policy

这套 5 根是本项目今后的正式 root taxonomy v1.0。

---

## 5. Level-2：19 个二级机制（冻结版 v1.0）

### R1 Information / Inference（4）

1. `R1.1` 同信息集下的估计器优势
2. `R1.2` 基本面/事件信息优势
3. `R1.3` 公开信息处理/文本信息优势
4. `R1.4` 覆盖不对称：小众/低覆盖/私有或提前信息

### R2 Pricing / Microstructure（4）

5. `R2.1` Sharp/consensus reference residual
6. `R2.2` Behavioural / demand shading
7. `R2.3` Market-type / odds-bucket / bookmaker structural bias
8. `R2.4` Opening/dispersion/cross-market relative pricing

### R3 Product / Contract（4）

9. `R3.1` 同赛事多玩法 probability/payoff consistency
10. `R3.2` M串N / component decomposition / parlay structure
11. `R3.3` Dependence / correlation mispricing
12. `R3.4` Settlement nonlinearity：rounding/cap/void/refund/rule mapping

### R4 Timing / Access / Execution（4）

13. `R4.1` Sharp lead-lag / stale quote
14. `R4.2` Lineup/news/event reaction lag
15. `R4.3` Opening/locked-price timing
16. `R4.4` Closing/cutoff/execution-window dynamics

### R5 External / Mechanical（3）

17. `R5.1` Official promotion / temporary subsidy
18. `R5.2` System / pricing / settlement error
19. `R5.3` Rebate / commission / outside transfer

`N_sub = 19`

---

## 6. Level-3：策略族数量

由于“策略族”拆分粒度天然不唯一，不宣称数学唯一。

在冻结以下计数规则后：

> 数据需求、decision timestamp、合同、动作方式中至少有一项实质不同，才算新 strategy family；
> 仅算法名字不同不计；仅联赛/赔率桶不同不计；仅 threshold 不同不计。

当前合并六份外部 AI 后得到：

`N_strategy_family ≈ 32`

推荐写法：

> **32 个冻结策略族（v1.0 counting convention）；合理拆分区间约 28–33。**

不要以后把“32”当成自然常数。

---

## 7. 32 个策略族（canonical merge v1.0）

### R1 — Information / Inference（8）

- `A01` Poisson/DC/Elo/xG/Bayes/ML outcome model
- `A02` Market + feature residual model
- `A03` Player / lineup / roster / tactical structured model
- `A04` Rest / travel / congestion / motivation
- `A05` Weather / pitch / referee / venue
- `A06` Public news / coach comments / social / text extraction
- `A07` Low-coverage leagues / newly listed competitions
- `A08` Private / non-public early information — OUT OF CORE / non-scalable

### R2 — Pricing / Market Microstructure（7）

- `B01` Same-time Sporttery vs sharp consensus residual
- `B02` 1X2 vs AH / O-U / exchange cross-market probability mapping
- `B03` Favourite-longshot / draw bias
- `B04` Home / national / brand / popularity bias
- `B05` Demand-driven shading / odds-bucket bias
- `B06` Opening-price systematic mapping bias
- `B07` Venue/bookmaker price dispersion / direct cross-market arbitrage scan

### R3 — Product / Contract（9）

- `C01` Same-event cross-play probability consistency
- `C02` Basic M串1 pricing consistency
- `C03` M串N component-set pricing
- `C04` Cross-match dependence / correlated legs
- `C05` Same-match dependence
- `C06` Rounding
- `C07` Prize cap
- `C08` Void / cancellation / refund
- `C09` Settlement / line-equivalence / ruleset-version mapping

### R4 — Timing / Access / Execution（5）

- `D01` Sharp lead-lag / stale quote
- `D02` Lineup/news/event reaction lag
- `D03` Early quote / price-lock timing
- `D04` Pre-close / cutoff drift
- `D05` Terminal / execution latency anomaly

### R5 — External / Mechanical（3）

- `E01` Official prize promotion / temporary subsidy
- `E02` System misquote / settlement anomaly
- `E03` Rebate / commission / outside bonus

总计：

`8 + 7 + 9 + 5 + 3 = 32`

---

## 8. Overlay / Modifier：不再重复计数

每条 strategy family 都可以附加：

### M1 Segment
- league
- team
- odds bucket
- favourite/longshot
- home/away
- schedule state
- market type

### M2 Time
- open
- T-24h
- T-6h
- lineup
- T-30m
- cutoff

### M3 Reference
- sharp bookmaker
- consensus
- exchange
- AH-derived
- closing

### M4 Execution
- single availability
- forced parlay
- cutoff
- max ticket
- max prize
- sales terminal
- ruleset version

### M5 Estimator
- Poisson
- Bayes
- XGB
- LLM
- ensemble

这些 overlay 不增加 root / family 数量。

---

## 9. 六份外部 AI 真正一致的地方

### 9.1 Generic model competition 被一致降级

6/6 都认为：

- Poisson
- Bayes
- XGB
- NN
- LLM/Agent
不是独立 edge 来源。

多数报告同时认为，在竞彩高摩擦下，纯公开历史数据模型即使预测指标改善，也很难转成经济 edge。

裁决：

`R1 GENERIC MODEL = DOMINATED / REVALIDATE`

不是数学意义 STRUCTURALLY KILLED。

只有 Oracle / actual execution hurdle 证明上界 <= 0，才能真正 KILL。

### 9.2 Stale price / lead-lag 是最稳定的幸存共识

几乎所有报告都保留：

- Sporttery vs sharp 同时点偏差
- sharp move → Sporttery repricing lag
- lineup/news → quote update lag

裁决：

`R4.1 / R4.2 = SURVIVES / REVALIDATE`

这是目前最值得继续实证的根之一。

### 9.3 Product / contract 是第二个共同幸存方向

主要包括：

- cross-play consistency
- M串N
- correlation
- rounding / void / cap

但外部报告普遍混入规则误判。

当前官方已确认：

> 同一场比赛不同玩法不能混合过关。

这 **KILL** 的是：
`same-match multi-play PARLAY`

不是：
`same-match cross-play CONSISTENCY TEST`

如果不同玩法分别有单关可买，仍然可以用 separate tickets 研究 synthetic payoff / consistency。

因此：

`C01 SURVIVES CONDITIONALLY`
`C05 PARLAY FORM KILLED BY RULE`
`C05 SEPARATE-SINGLE FORM DEPENDS ON AVAILABILITY`

### 9.4 External/Mechanical 一致被判断为非核心

包括：
- rebates
- bugs
- arbitrary promotions
- settlement anomalies

共同特点：
- rare
- low capacity
- rule/compliance dependent
- 不代表足球预测能力

裁决：

保留在 taxonomy，默认 P2/P3，不进入主研究预算。

---

## 10. 六份报告最有价值的独特贡献

### EAI-01（4 根）
优点：
- 最强的第一原理压缩；
- 正确指出 timing/segmentation/model 可能只是实现层。

缺点：
- 对旧路“结构性 KILL”过于激进；
- 使用未经锁定的 margin 数值做裁决。

用途：
`机制压缩参考`

### EAI-02（5 根，约25–30族）
优点：
- 结构接近最终 5 根；
- coverage 较广。

缺点：
- 当前制度数字过时；
- 73%/72–73% 与当前 70% 不符；
- 将制度返奖与单场 overround 混用；
- 同场混串等执行假设不严谨。

用途：
`路线覆盖参考`

### EAI-03（7 根）
优点：
- 暴露出 cross-market、segmentation 这些边界争议；
- route list 有补充价值。

缺点：
- `Conditional` 错升为 root；
- `Cross-market` 错升为 root；
- root/sub 计数内部不一致；
- hurdle 推导错误。

用途：
`反例/过度拆分样本`

### EAI-04（5 根，14族）
优点：
- 明确把 segmentation 降级；
- 最简洁的 applied taxonomy。

缺点：
- N_sub 自报 14，树上实际 15；
- 制度数字仍错误；
- 对可执行性判断缺乏官方规则校验。

用途：
`简化结构参考`

### EAI-05（6 根，33族）
优点：
- route coverage 最丰富；
- 对容量、拒注、执行限制有意识；
- 提出“测量而非预测”的方向。

缺点：
- 最大硬伤：把 2014 年 73% 当当前规则；
- 进一步推导 38.9% hurdle，基础错误；
- 把 0.72^n 当通用串关真实成本，过度简化；
- 把 1% 调节基金当当前制度，过时；
- “单票 2 万”类容量数值与现行 6000 元规则不符；
- 因错误 hurdle 导致大量 route 被过早 KILL。

用途：
`route inventory`
而不是 verdict。

### EAI-06（edge-space-enumeration-report-v1）
优点：
- 六份里方法论最强；
- 明确发现“制度返奖率 != 定价 overround”；
- 引入 detectability / STRUCTURALLY UNVERIFIABLE；
- 区分 information-set advantage 与 inference advantage；
- 使用我方 legacy inventory 做可测性映射；
- 明确 segmentation 不是 root；
- 把最关键实测压缩为“Sporttery vs sharp same-time residual distribution”。

缺点：
- 部分规则在报告中仍标 UNKNOWN，现已可用官方源关闭；
- 引用旧资产中的数值仍需独立 QA；
- 与 legacy E54/E55 已做过的 negative experiment 尚未完整 crosswalk；
- S9 “同场跨玩法”需要加入当前“同场不可混串 + 单关可得性”执行约束。

裁决：

`BEST FRAMEWORK INPUT`
但不是最终结论。

---

## 11. 旧研究与外部 AI 的交叉核对

旧资产已经包含的研究远比外部 AI 假设的多。

### 已有资产/实验覆盖

根据 inventory：

- `e58_census_odds.csv`：60 万级全玩法历史赔率
- `fb_ttg_series.csv`：16 万级 ttg 调价时点
- `e54_join.csv`：竞彩 × Pinnacle 严格配对
- CLV ledger
- 多组 Oracle / overround / 全玩法 census
- 外部盘口
- 跨玩法
- timing / CLV
- 分联赛校准
- FLB
- 单关可得性

### 已知旧结论

旧《结案报告》记录：

- Pinnacle ttg 增量信息实验：negative
- 跨玩法 1X2 → ttg：negative
- 分联赛校准：negative
- timing / CLV：仍有较大 hurdle gap
- generic model routes 多次 negative
- 单关 availability 是关键结构变量

### 但旧研究有已知重大 bug

inventory 已确认：

- BUG-001 ROI 分母错误：+4844% → 约 -18%
- BUG-002 hit mask 漏乘：+549% → 约 -18%
- BUG-004 排序错位：+15.12% → -16.17%
- 另有 merge/join/meta/ledger 问题

因此对旧结论使用：

- corrected negative evidence：可以降级路线；
- 未完全复现：不能升级为 theorem；
- 涉及 affected experiment：`REVALIDATE`

### 重要推论

外部 AI 的“generic model 大概率不值继续投入”与旧研究方向一致。

但：

> 不能因为六个 AI 都说“模型死了”，就宣布数学死亡。

正式状态应是：

`DOMINATED / REVALIDATE`
直到：
- actual current hurdle
- True-Probability Oracle
- Public-Information upper bound
三层都锁定。

---

## 12. 当前 provisional route status（冻结前版）

### P0 — 必须完成，信息价值最高

#### `B01 / D01`
Sporttery vs sharp **同时点 residual + lead-lag**

状态：
`SURVIVES / REVALIDATE`

理由：
- panel 最高共识；
- legacy 做过 ttg/Pinnacle，但不是全 root 穷尽；
- timing alignment 是核心；
- 当前数据资产可能已有部分基础。

#### `C01`
同赛事多玩法 internal consistency

状态：
`SURVIVES CONDITIONALLY`

理由：
- deterministic / low-cost；
- 不需要先建足球预测模型；
- 但必须加：
  - same-match parlay prohibition
  - single availability
  - same timestamp
  - same ruleset

### P1 — 条件保留

- `D02` lineup/news lag
- `B03/B04/B05` behavioural/demand shading
- `C03/C04` M串N / cross-match dependence
- `A07` low-coverage leagues
- `A02` market + public feature residual

### P2 — 默认降级

- generic model replacement
- further model complexity
- LLM multi-agent prediction
- generic FLB migration from overseas
- early/late timing without mechanism
- rounding/cap as “main edge”

### OUT OF CORE

- private/inside information
- overseas execution arbitrage
- unofficial rebates
- system-exploit hunting

---

## 13. 下一步为什么需要 legacy evidence，而不是继续抽象理论

到这里：
- root 边界已稳定；
- sub-mechanism 已冻结；
- strategy-family counting convention 已冻结；
- 官方当前规则冲突已关闭；
- 外部 AI 分歧已解释。

继续做 taxonomy 的边际收益很低。

下一步应做：

`EDGE_EXHAUSTION_MATRIX v1`

逐项把：
- 32 strategy families
映射到：
- legacy experiment
- evidence path
- bug exposure
- actual hurdle
- availability
- N_eff
- Oracle upper bound
- current status
- kill/reopen criteria

这一步不能再只靠理论。

如果 raw legacy assets / experiment outputs 尚未全部可直接读取，
则需要 WorkBuddy staging / evidence export。

---

## 14. 本轮最终裁决

### 数量答案

如果问：

> “正 EV 的数学根源到底有几种？”

答：

`3 个 algebraic primitives + 1 个 feasibility dimension`

如果问：

> “为了竞彩足球研究，应该分成几条根级研究路线？”

答：

`5 个 applied research roots`

如果问：

> “穷举以后具体可研究路线大约有多少？”

在冻结 v1.0 计数规则下：

`19 个 sub-mechanisms`
`32 个 strategy families`
合理粒度区间约：
`28–33 个`

### 最重要的修正

1. 删除 Conditional/Segmentation root。
2. 不把 Cross-market arbitrage 作为 root。
3. 保留 Timing 作为 applied root，而非 algebraic root。
4. 当前返奖率按 70%，不是 73%。
5. 70% 不直接等于单场 30% margin。
6. route kill 必须用 actual executable hurdle，不用制度返奖比例硬推。
7. 同场不同玩法不可混串，但 cross-play consistency 并未因此全部死亡。
8. generic model routes 降级为 DOMINATED/REVALIDATE，而不是凭文献“数学死亡”。
9. stale-price / same-time sharp residual 与 cross-play consistency 是最值得先证伪的两个结构问题。

---

## 15. 状态

`EXTERNAL_AI_PANEL_SYNTHESIS = COMPLETE`

`APPLIED_EDGE_TAXONOMY_V1 = FROZEN`

`NEXT = LEGACY_EVIDENCE_INGESTION / EDGE_EXHAUSTION_MATRIX`
