# GitHub 开源项目侦察：竞彩足球 / 足球概率 / 赔率研究

- 日期：2026-09-22
- 项目：football-betting-research
- 类型：External Reconnaissance / GitHub Scout
- 版本：v3.0 — External AI Panel Synthesis / Applied Edge Taxonomy v1
- 状态：Active reconnaissance record, pending repository sync
- 说明：v1 为候选项目侦察；v2 开始区分 README 级信息与源码/测试/issue 级证据。只有达到足够证据等级的项目才允许影响正式架构决策。

## 结论摘要

本轮最重要的结论不是“找到一个神项目”，而是确认未来项目应采用“拼积木”路线：

1. 足球概率与赔率基础数学不应从零重写。
2. 数据层应采用 source adapter -> raw snapshot -> normalized long/tidy schema -> derived research table。
3. 回测器必须把防未来泄漏设计成结构性约束，而不是靠研究者自觉。
4. 评价不能只看 ROI；必须同时看校准、CLV、bootstrap CI、按比赛聚类后的不确定性。
5. “竞彩价差”应被做成独立的价格比较/信号层，而不是混入预测模型。
6. 实盘运行应采用事件驱动 + paper/影子模式 + rejection log + exposure limit。
7. 竞彩官方数据链已经有多个公开实现，可借鉴接口、字段和单关/过关规则，但不能盲信其“价值判断”或去水方法。
8. 旧项目中“自己做很多基础数学与回测 plumbing”的比例应下降，把精力转向：时间一致性、数据对齐、市场结构、可执行性和前瞻验证。

## 审计证据等级

从 v2 起，所有开源项目按以下证据等级记录，避免把 README 宣传当成已验证事实：

- **SCOUTED**：只确认仓库、README、文档、活跃度和大致方向；只能进入候选池。
- **PARTIAL AUDIT**：已检查部分核心源码、测试、release/issue 或数据流；可以形成具体工程启发，但仍不能整体信任。
- **AUDITED CORE**：与我们拟复用部分直接相关的核心实现、测试和主要失败模式均已检查；可以进入“待复现/待集成”候选。
- **REPRODUCED**：已在我们的环境中 clone/运行测试或样例，关键行为可复现。
- **ADOPT / REJECT**：经过本项目独立 QA 后，才允许正式采用或明确拒绝。

原则：**项目知名度、Star 数、README 中的收益结果，均不提高证据等级。**

### v2 当前状态

| 项目 | v1 状态 | v2 证据等级 | 变化 |
|---|---:|---|---|
| `martineastwood/penaltyblog` | 候选 | **PARTIAL AUDIT** | 已读 Dixon-Coles/Poisson 核心实现与 release bug 记录；可作 reference，但必须锁版本+自建 golden tests |
| `Johnserf-Seed/SportteryAPI` | 候选 | **AUDITED CORE** | 已读 `derive.ts`、`parse.ts`、`upstream.ts`、MCP 与 parse tests；采集/解析层价值高，概率语义需修正 |
| `probberechts/soccerdata` | 候选 | **PARTIAL AUDIT** | 已读 scraper 代码、测试/DVC 机制、PR/issue；provider/caching 模式可靠，外部源脆弱性明显 |
| `thewongdirection/soccer-betting-strategy` | 候选 | **PARTIAL AUDIT** | 已确认目录/数据模式/跨源 key 设计与实验结构；仓库仅少量提交且缺少可见系统测试，结果只能视为作者报告 |
| `R1ch1k/betting-backtester` | 候选 | **PARTIAL AUDIT** | 已确认仓库有 `src/`+`tests/` 及详细设计声明；核心源码尚未逐文件完整取得，不能升级为 AUDITED |
| `GitSimaao/proofodds` | 新发现 | **SCOUTED+** | 赛前封存、hash chain、独立重算 score 的思想高度相关，待源码审计 |
| `gcunharodrigues/sports-betting-ml-audit` | 新发现 | **SCOUTED+** | 负结果与方法论审计极相关，已读完整研究说明但尚未逐实验脚本审计 |
| `mberk/shin` | 新发现 | **AUDITED CORE** | 已读 Python 核心实现与 `test_shin.py`；Python/Rust 路径均有数值测试。发现默认调用会丢弃未收敛诊断，必须由我们包装 fail-closed |
| `D4Vinci/Scrapling` | 新发现 | **SCOUTED / NOT ADOPTED (CURRENT SCOPE)** | 已完成 README/文档级能力与边界侦察，并在本地用现有 `lxml` 复现其声明式解析思路；当前不安装、不采用。反检测/挑战求解/代理轮换不解决当前 provider-timestamp 瓶颈，且触及项目红线。若未来出现具体唯一用例，先对所需组件做 PARTIAL AUDIT，再讨论采用。 |

## 高价值项目

| 项目 | 主要价值 | 对我们的启发 | 风险/限制 | 优先级 |
|---|---|---|---|---|
| `martineastwood/penaltyblog` | Poisson、Dixon-Coles、Bayesian、AH/OU、implied probability、ratings | 基础数学不再从零实现；作为 baseline/reference oracle | 成熟库也修过 quarter-line 与 AH sign bug，必须版本锁定+回归测试 | P0 |
| `probberechts/soccerdata` | 多源足球 scraper、统一 DataFrame、缓存 | 正式建立 `providers/`，抓取与研究解耦；默认离线复现 | 外部站点会变，provider 仍需健康监控 | P0/P1 |
| `thewongdirection/soccer-betting-strategy` | football-data + Singapore Pools/sgodds 统一 schema | SP 与 sharp market 进入同一“价格语言”；match key/alias/timezone 做基础设施 | 很新、提交少，理念可借，代码需独立审计 | P0 概念 |
| `R1ch1k/betting-backtester` | walk-forward、match-level bootstrap、Strategy protocol、lookahead guard | 新回测器走 event-driven；防泄漏做成接口约束；保存 rejection log | 很新，不能直接等同成熟库 | P0 |
| `sparegk/odds-quant` | timestamped snapshots、VALUE/WATCH/PASS、freshness/uncertainty blocking | 把 T1/T2/T3 改造成 signal state machine；PASS 成为一等结果 | 许多内容是 roadmap/architecture | P0/P1 |
| `mperi1208/value-bet-model` | 公开数据 value betting 的系统失败案例 | 增加 selection-conditioned calibration；edge monotonic sanity test；calibration/test 分离 | 结果只适用于其数据/模型 | P0 方法论 |
| `vladapl21/odds-calibration` | 长期市场效率、模型与 market baseline 对比 | 每个模型首先必须打 market baseline，而非 random | 英超市场不代表所有竞彩市场 | P1 |
| `betcode-org/flumine` | event-driven 交易框架、paper、simulation、risk、workers | 未来 24h runtime 借“框架管运行、strategy 管决策” | 主要面向交易所，不是竞彩 | P1 |
| `AnishKhetani/premier-league-data` | raw/processed、stable id、schema spec、可重建、Actions refresh | 数据 pipeline 可审计；大数据与代码/manifest 分离 | EPL 单联赛 | P1 |
| `gotoConversion/goto_conversion` | Shin / favourite-longshot bias / alternative de-vig | 去水方法成为实验变量；benchmark proportional/power/Shin | 需确认不同市场适用性 | P1 |
| `jordantete/OddsHarvester` | OddsPortal upcoming/historical scraper | 可做补充历史侦察源 | ToS、反爬、页面变化；不宜做核心生产源 | P2 |
| `shangfangjian1993/sporttery-api` / `Johnserf-Seed/SportteryAPI` | sporttery web endpoint、pool parser、M串N、MCP、offline tests | 竞彩采集层不必从零猜接口；抓取与纯计算拆开；提前处理 geo-block | undocumented endpoint 会变；proportional no-vig 不能直接当真值 | P0 |
| `Mrio10086/football-3x4-skill` | 竞彩实时抓取、串关场景计算、Codex skill | 后期“已选比赛 -> 串关/金额/场景损益”可独立成工具 | “赔率涨跌=利好/利空”等不能当研究结论 | P2 |
| `excalibur-sa/football-lottery` | provider abstraction、mock provider、service/UI 分层 | 我们也应有 mock provider 支持 CI/离线测试 | 分析层较浅 | P2 |

## 关键方法论启发

### 1. 不再从零写基础足球数学

`penaltyblog` 已覆盖 Poisson、Dixon-Coles、Bayesian goal models、赔率去水、Asian handicap / totals 等。我们的精力应放在竞彩业务映射、数据 provenance、时间纪律、市场对齐、signal 与 QA。

但第三方库必须：
- 锁版本；
- 建 golden tests；
- 关键盘口与 quarter-line 自己做回归样例；
- 不把库输出当“真理”。

### 2. 新数据层采用 provider + raw cache + normalized schema

建议：

`provider -> raw snapshot -> normalization -> canonical odds/matches -> research tables`

每条外部数据保存：
- source
- provider_update_time
- collected_at
- effective_at
- raw hash
- parser version
- reliability/freshness state

赔率采用 long/tidy schema：

`match_id, source, bookmaker, market, selection, line, phase, odds, captured_at`

### 3. 回测防泄漏必须结构化

借鉴 `betting-backtester`：
- odds event
- prediction event
- decision event
- settlement event
- Strategy protocol
- strategy 不应直接获得未来 iterator
- deterministic replay
- rejection log
- match-level bootstrap CI

### 4. 增加“被选中下注样本”的校准检查

`value-bet-model` 的重要失败：全局 calibration 可以很好，但 BUY subset 可能系统性过度自信。

因此正式指标应包括：
- global Brier / log-loss / ECE
- BUY-subset calibration
- edge bucket calibration
- edge threshold vs realised ROI/CLV monotonicity

### 5. 市场必须是第一 baseline

模型评估顺序：
1. 去水后的市场概率；
2. trivial baseline；
3. Elo/Poisson/Dixon-Coles；
4. 才是复杂模型。

模型如果不能稳定改善 market log-loss/calibration，就不进入“价值投注”层。

### 6. Signal 不是一个 BET 布尔值

建议状态：
- PASS
- WATCH
- CANDIDATE
- BUY
- BLOCKED_STALE
- BLOCKED_UNCERTAIN
- BLOCKED_CALIBRATION
- INSUFFICIENT_DATA

每次状态变化必须有 reason codes。

### 7. 竞彩抓取层可以大量借鉴公开项目

现有公开实现已经覆盖：
- sporttery web endpoint
- HAD / HHAD / CRS / TTG / HAFU
- raw -> normalized parser
- per-odds trend flag
- 单关 / M串N 规则
- sample JSON / offline unit tests
- local MCP
- geo-block handling

但必须独立验证字段、规则与 endpoint 稳定性。

## 暂时不建议投入太多时间的方向

- 单纯优化 winner accuracy 的 ML 项目。
- 没有 point-in-time odds 的“高准确率预测”。
- 多 Agent / LLM 专家会诊式选球。
- 复杂 dashboard。
- 自动下注。
- 早期串关优化。

原因：这些都不能替代市场基线、时间一致性、校准、执行价格与前瞻验证。

## 对 `football-betting-research` 的建议模块边界

### `providers/`
Sporttery、sharp odds、football-data、soccerdata-supported sources、未来 xG/lineup source。只 fetch + parse。

### `raw_snapshots/`
外部输入原样保存 + 时间/哈希/版本元数据。

### `normalization/`
match identity、team aliases、timezone、market/selection/line/phase 统一。

### `pricing/`
implied probability、proportional/power/Shin 等去水、fair odds、盘口等价映射、cross-market consistency。

### `models/`
第一阶段仅 market、Elo、Poisson、Dixon-Coles。复杂 ML 必须证明 OOS 增量。

### `signals/`
状态机 + reason codes + freshness/uncertainty/blocking。

### `backtest/`
事件驱动、walk-forward、anti-lookahead、deterministic、rejection log、match bootstrap、selection-conditioned calibration。

### `execution_shadow/`
前瞻 BUY/PASS、decision cutoff、available SP、reference close、result、CLV、ROI、blocked/missed reason。

### `runtime/`
scheduler/stream、workers、retry、health、monitoring、notification。WorkBuddy 管运行 plumbing，不改策略。

## 当前建议

### 立即吸收
- `penaltyblog`：基础概率与 odds math reference implementation
- `soccerdata`：provider/caching pattern
- `betting-backtester`：event-driven + structural anti-lookahead + match-bootstrap
- `soccer-betting-strategy`：Pools vs sharp-market normalized schema 思路
- `SportteryAPI`：竞彩 endpoint / pool parser / parlay math
- `odds-quant`：signal state + freshness/uncertainty metadata

### 先研究后决定
- `goto_conversion` / Shin / power 去水比较
- `flumine` runtime architecture
- `OddsHarvester` 作为补充数据源

### 不急
- 深度学习预测赢家
- LLM 多 Agent 足球分析
- 复杂前端 dashboard
- 自动下注
- 串关优化

## 下一阶段顺序建议

旧资产整理完成后：
1. R1 — Research Charter
2. R2 — Public ecosystem / data-source reconnaissance
3. R3 — Market structure census
4. R4 — Canonical data & pricing layer
5. R5 — Backtester verification
6. R6 — Baseline market/model comparison
7. R7 — Candidate signal experiments
8. R8 — Prospective shadow ledger
9. R9 — Small-stake live execution

本文件属于 R2 的前置侦察素材。

## v2 源码级审计记录

> 本节覆盖 2026-09-22 的第二轮深挖。除非明确写为“源码观察”，README/作者给出的历史收益、测试数量、回测结果一律只作为**作者声明**，不作为我们项目的复现证据。

### A1. `martineastwood/penaltyblog` — PARTIAL AUDIT

**已实际检查**

- `penaltyblog/models/dixon_coles.py`
- `penaltyblog/models/poisson.py`
- release notes / compatibility fixes

**源码观察**

1. `DixonColesGoalModel` 不是一个薄封装。实际实现包含：
   - attack / defence / home-advantage / `rho` 参数；
   - 和为常数的参数约束；
   - 参数 bounds；
   - 解析梯度，并明确处理“优化负 log-likelihood 所以梯度取负”；
   - neutral venue 时关闭主场优势；
   - 单场与 batch probability grid 两套路径；
   - 低层概率函数与预分配数组以减少重复分配。
2. Poisson 与 Dixon-Coles 共享相似的 probability-grid 抽象，说明其“模型 → 统一比分概率网格 → 派生市场概率”的架构值得参考。
3. release 历史不是只加功能，也记录过会直接改变投注结论的严重 bug：
   - 四分之一大小球 split-stake / push 逻辑曾错误；
   - Asian handicap 正负号曾反转，导致 win/lose probability 对调；
   - SciPy 优化器版本变化曾迫使项目钉住兼容版本。
4. 因此，“成熟库”最多意味着代码积累较多，**不等于盘口数学永远正确**。

**对我们的具体决定**

- 不再从零重复实现 Poisson / Dixon-Coles 核心拟合。
- `penaltyblog` 作为 **reference oracle / baseline**，不是唯一真值。
- 我们必须自己保存一组 hand-calculated golden fixtures，覆盖：
  - 1X2；
  - AH 0 / ±0.25 / ±0.5 / ±0.75 / ±1；
  - O/U 2.0 / 2.25 / 2.5 / 2.75 / 3.0；
  - push / half-win / half-loss；
  - neutral venue。
- 依赖必须版本锁定，升级 `penaltyblog/scipy/numpy` 时先跑 regression gate。
- 模型训练时间窗、数据 provenance、as-of 时间仍由我们自己控制，第三方库不负责这部分。

**暂不做**

- 不直接复制其内部优化代码进入我们的 repo。
- 不因为 `penaltyblog` 输出某个概率就跳过我们自己的市场/时间校验。

---

### A2. `Johnserf-Seed/SportteryAPI` — AUDITED CORE

**已实际检查**

- `src/derive.ts`
- `src/parse.ts`
- `src/upstream.ts`
- `mcp/server.ts`
- `mcp/sporttery.ts`
- `test/parse.test.ts`
- 项目结构与 offline sample/CI 说明

**源码观察：赔率数学**

`derive.ts` 明确实现的是最简单的比例去水：

- `implied = 1 / odds`
- `overround = Σ implied`
- `noVig = implied / overround`
- `fairOdds = 1 / noVig`

这应命名为 **proportional no-vig / 归一化市场概率**，不应在我们系统中直接叫“真实概率”。

`compareOdds()` 把 reference odds 的比例去水结果作为比较基准。源码注释甚至称其为 `"true" probabilities`。对我们的研究语义而言这过强：**reference market probability ≠ ground truth probability**。

**源码观察：一个值得警惕的细节**

`deriveMarket()` 会忽略无效/缺失赔率，再对剩下的 outcome 计算 overround；`parse.ts` 同样会跳过“未报价 outcome”，只要还剩至少一个 outcome 就继续生成 market 并派生概率。

这在工程上“尽量返回数据”很方便，但在固定 outcome 市场里可能危险：

- 1X2 如果缺一项，剩余两项归一化后仍会得到一个看似正常的和为 1 的 `noVigProb`；
- 但这不是完整市场的公平概率。

**我们的规则必须比它更严格：固定 outcome market 缺项时 fail closed，禁止产生 fair probability / EV。**

**源码观察：抓取与时间**

- upstream 指向 Sporttery calculator 使用的公开 web endpoint；
- 内置 Cache / proxy / browser-like headers；
- 项目明确知道 datacenter / Cloudflare geo-block 风险；
- parser 保存 market `updateTime`，payload 还有 `lastUpdateTime`；
- 但它主要提供“当前最新快照”，不是历史 append-only snapshot ledger。

**测试观察**

`parse.test.ts` 确实用 captured `sample.json` 离线测试：

- HAD outcome 顺序；
- return rate 合理范围；
- no-vig 和约等于 1；
- pool/date/matchId filter；
- HHAD goalLine。

这证明“抓取 I/O 与纯解析/数学分离”不是 README 口号，代码与测试都存在。

**对我们的具体决定**

可以借：

- Sporttery pool mapping / labels；
- parser 组织方式；
- live I/O 与 pure math 分离；
- MCP 工具层；
- sample payload 离线测试；
- proxy / geo-block 失败处理思路；
- M串N / 奖金计算作为后期执行工具的参考。

必须改：

1. “真实概率”统一改为 `market_reference_probability` / `proportional_no_vig`。
2. 固定 outcome market 必须验证 expected selection set 完整。
3. 每次采集保存：
   - raw bytes / raw JSON hash；
   - `observed_at`（我们看到它的时间）；
   - source `updateTime`；
   - HTTP/source metadata；
   - parser version。
4. undocumented web endpoint 只作为一个 provider，不允许成为唯一事实源。
5. 对 endpoint schema 建 fingerprint / contract test；shape 变化必须报警而不是静默解析。

**当前判断**

SportteryAPI 的**竞彩数据工程核心值得直接借鉴设计思想**；赔率“价值判断”层不采信。

---

### A3. `probberechts/soccerdata` — PARTIAL AUDIT

**已实际检查**

- repository layout（838 commits，独立 `soccerdata/`、`tests/`、`.dvc`、docs）
- `soccerdata/fbref.py`
- `CONTRIBUTING.rst`
- 与 scraper 变化相关的 PR / issue

**源码/工程观察**

1. FBref scraper 本身超过千行，基于统一 reader 基类、缓存目录、标准化列名、team-name 替换等公共设施；这说明 provider adapter 并不是 README 层概念，而是成熟代码结构。
2. 测试数据通过 DVC 管理，目的明确：CI/本地测试用固定缓存数据，不需要每次测试都在线抓网站。
3. PR 中可以看到 scraper 修改同时伴随 tests 修改，说明维护流程相对成熟。

**issue 反过来给我们的重要证据**

公开 issue 显示现实世界的数据源会以各种方式失效：

- HTTP 503；
- 403 / captcha；
- 页面结构/API 数据字段变化；
- CSV 编码/BOM 等看似微小但会破坏 schema 的变化；
- source-specific parser 随网站升级而失效。

这比“支持很多数据源”本身更重要。

**对我们的具体决定**

采用其模式但再加一层审计：

`provider -> immutable raw snapshot -> parser(versioned) -> normalized record`

并新增：

- provider health state；
- schema fingerprint；
- parse error rate；
- last successful fetch；
- raw snapshot hash；
- cache freshness；
- fail-closed on silent schema drift。

研究/回测不得依赖“今天网站还能抓到什么”；应默认从已经冻结的 raw snapshot 离线重建。

**当前判断**

`soccerdata` 可以成为 provider-interface 和测试缓存设计的主要参考，但不是数据真实性担保人。

---

### A4. `thewongdirection/soccer-betting-strategy` — PARTIAL AUDIT，较 v1 降级

**已检查**

- repo tree / scripts / `soccer_backtest` 模块划分；
- normalized matches/odds schema；
- football-data + sgodds 数据流；
- match key / alias 的公开实现说明；
- Strategy 1/2/3 的运行逻辑与作者报告结果；
- known limitations。

**值得保留的设计**

赔率 long/tidy schema 仍然很适合我们：

`match_key, source, league, season, date, home, away, bookmaker, market, selection, line, phase, odds`

raw cache 与 processed Parquet/SQLite 分离也合理。

**但源码审计思维下出现两个明显风险**

#### 风险 1：`match_key` 刻意不含日期

作者为解决 SGT 与本地比赛日期跨日问题，用：

`league + season + canonical home + canonical away`

来生成跨源 match key。

这很聪明，但对我们不够安全。因为：

- playoff / cup / two-leg / 重赛 / 某些赛制可能在同 season 出现相同 home-away；
- 错误 alias 可能制造碰撞；
- “100% reconciliation”并不能证明每个 join 是正确的一对一匹配。

**我们的设计：**
- provider event ID 尽可能保留；
- canonical fixture ID 不能只靠 home-away-season；
- 使用 kickoff UTC + 容差窗口 + competition + teams；
- 所有 cross-source join 必须 assertion：
  - one-to-one cardinality；
  - no collision；
  - 时间差阈值；
  - unmatched / ambiguous 显式输出。

#### 风险 2：`phase=open/close` 太粗

sgodds 自身说明其 Singapore Pools 当前赔率可能比官方约滞后约 10 分钟。仅存 `phase=open`，不足以做我们需要的赛前价格研究。

**我们的 odds schema 必须增加：**

- `observed_at`
- `source_updated_at`
- `provider_event_id`
- `provider_market_id`（有则保留）
- `is_opening / is_closing` 只作为派生标签，不代替真实时间。

**对作者实验结果的证据降级**

其 Poisson、Dixon-Coles、CLV、EPL 不可击败等结果目前仍主要来自仓库作者的报告。仓库仅少量 commits，未见与成熟项目相当的独立系统测试证据。

因此这些结果只用于：
- 提醒我们设计反例；
- 作为待复现 benchmark；

**不能作为“市场已经证明不可打败”的项目事实。**

**当前判断**

架构启发：高。  
研究证据：低到中。  
代码复用：暂缓。

---

### A5. `R1ch1k/betting-backtester` — PARTIAL AUDIT，继续列为高优先级待复现

**已经确认**

仓库真实存在：
- `src/betting_backtester/`
- `tests/`
- `data/`
- `docs/`
- scripts / pyproject / lockfile。

作者公开设计包括：

- `Strategy.fit / on_odds / on_settled`
- event-by-event simulation
- rolling walk-forward
- match-level bootstrap
- rejection log
- bankroll invariants
- UTC-only event types
- commission per market
- synthetic deterministic generator
- deterministic output tests
- regime-reversal anti-lookahead test
- 明确声明不模拟 live slippage / latency / partial fills。

**目前不能升级到 AUDITED CORE 的原因**

GitHub 搜索索引暂时没有稳定给出其核心 `backtester.py` / `walk_forward.py` / test 文件全文，本轮还没有逐函数验证作者对“~800 tests”“regime-reversal”“byte-identical”的声明。

所以：
- 这些设计理念非常值得我们独立实现；
- 但不能写成“我们已经验证该仓库确实完全做到”。

**一个即使源码实现正确也仍然存在的理论缺口**

“策略拿不到 future event iterator”只能防**事件序列层**泄漏。

它不能自动防止训练表本身已经混入未来信息，例如：

- 赛后才修订的 xG；
- 后补的阵容；
- 最终 closing odds 被错当成 decision-time feature；
- derived table 在构建时用了未来数据。

因此我们的 anti-lookahead 要分两层：

1. **event-order guard**
2. **feature as-of/provenance guard**

后者必须由数据层承担，不能只交给 backtester。

**当前判断**

仍是我们回测器最值得进一步 clone/reproduce 的候选之一。下一步应直接运行其 tests 并读核心 source 后再决定“借接口还是直接依赖”。

---

## v2 新发现：可能改变我们项目审计体系的项目

### B1. `GitSimaao/proofodds` — SCOUTED+，高优先级

这个项目最值得我们的不是预测模型，而是**证明预测确实在赛前产生且没有被赛后改写**的机制。

公开设计包括：

- 每个 matchday 的预测文件在 kickoff 前写入；
- 已存在的日期文件不修改；
- ledger entry 串接前一 entry 的 SHA-256，形成 hash chain；
- entry 记录生成代码的 Git commit、dirty flag、source digest；
- 每日 push 到 public Git；
- 进一步用 OpenTimestamps 对 JSON 做外部时间证明；
- `verify.py` 使用独立、stdlib-only 的验证实现；
- `rescore.py` 用第二套实现重新计算成绩，避免“同一段代码自己证明自己”。

**对我们的启发非常大。**

我们未来的 prospective shadow/live ledger 建议至少采用：

1. 决策 cutoff 前生成 canonical JSON；
2. 写入：
   - fixture id；
   - observed input hashes；
   - model/rule version；
   - BUY/PASS；
   - probability / price / reason codes；
   - generated_at；
   - git commit；
3. SHA-256 seal；
4. append-only chain；
5. 赛后只追加 settlement，不修改 pre-match record；
6. Reviewer 可以独立 `verify` / `rescore`。

OpenTimestamps/Bitcoin anchor 可以以后再决定；**先有 append-only + hash chain + Git commit 就已经比普通 CSV ledger 强很多。**

这可以有效解决我们项目一个长期风险：

> “赛后是不是无意中修订了历史预测？”

**注意**

目前主要依据其公开技术说明，核心 ledger/verify 源码尚未完整逐文件审计，所以暂列 SCOUTED+，不能称已验证。

---

### B2. `gcunharodrigues/sports-betting-ml-audit` — SCOUTED+，方法论高价值

这个仓库价值在于**系统保存失败结果**，而不是发布“赚钱模型”。

其公开研究对 football / tennis / horse racing 做 walk-forward，并把自己发现的错误模式列出来：

1. uncontrolled multiple comparisons；
2. bookmaker margin removal 不一致；
3. temporal feature engineering 破坏；
4. sample size 太小；
5. post-hoc threshold cherry-picking。

足球实验中作者还展示：大量 threshold/model variant 扫描里少数正 ROI 不稳定，多重比较校正后不成立。

**这与我们旧项目历史 bug/研究纪律高度相关。**

对我们的具体约束建议新增：

- 每个 experiment 预先登记 hypothesis / primary metric / threshold family；
- 参数 sweep 必须记录完整 family，不能只保存 top result；
- 有多个 threshold/config 时做 Bonferroni/FDR 或明确当 exploratory；
- “34 个负结果 + 2 个正结果”不能只拿 2 个正结果讲故事；
- 失败实验必须进入 evidence registry；
- de-vig method 必须统一版本化；
- temporal feature build 也要单独测试。

**注意**

当前仍是研究说明/审计报告级检查，实验脚本还未逐文件重跑，所以不能把它的“所有 ML 都不赚钱”当作我们的结论。

---

### B3. `mberk/shin` — SCOUTED+，建议替代 v1 中的泛化去水候选

相较 `goto_conversion`，这个仓库更适合作为 Shin 方法的专门 reference：

- 79 commits；
- 有 tests / CI；
- 给出原始学术引用；
- 返回 convergence diagnostics；
- 两 outcome 有解析处理；
- Rust optimizer + Python fallback；
- 输出 `iterations / delta / z`，可以明确检测未收敛。

**对我们的影响**

`pricing/` 不应只有 proportional 去水。建议形成标准 benchmark：

- proportional
- additive
- power
- Shin

但去水方法的角色必须定义清楚：

> 它们是在推断“市场共识概率”的不同假设，不是比赛真值模型。

任何 de-vig 方法都不能自动等同于公平真实概率。

---

## v2 对项目路线的新增修正

### 1. 加入 `evidence_level`

外部依赖/研究灵感登记时必须带：

- `SCOUTED`
- `PARTIAL_AUDIT`
- `AUDITED_CORE`
- `REPRODUCED`
- `ADOPTED/REJECTED`

后续架构文档引用外部项目时，必须同时写证据等级。

### 2. 数据完整性改为 fail-closed

尤其对固定 outcome market：

- 缺任何 selection；
- outcome 数量异常；
- join cardinality ≠ 1:1；
- fixture collision；
- source timestamp 不合理；

一律不能继续算 fair probability / EV，只能进入 blocked/quarantine 状态。

### 3. 区分三个“概率”

以后变量名和报告禁止混用：

- `raw_implied_probability`
- `market_reference_probability`（去水后）
- `model_probability`

只有比赛赛果是最终观测；market reference 不叫 `true_probability`。

### 4. anti-lookahead 双层防线

必须同时做：

- **事件序列防泄漏**：decision 看不到未来 event；
- **特征 as-of 防泄漏**：每个 feature 有可证明的 available_at/source snapshot。

### 5. prospective ledger 加“不可篡改证据”

受 `proofodds` 启发，R8 shadow ledger 的最小规范增加：

- canonical serialization；
- SHA-256；
- previous-record hash；
- generated_at；
- git commit / ruleset id；
- input snapshot hashes；
- append-only settlement；
- 独立 verify command。

目标不是玩区块链，而是让“赛前已经作出什么决定”成为可验证事实。

### 6. 外部项目结论只允许两种进入方式

- **工程模式**：我们自己读代码/测试后借鉴；
- **研究结论**：必须在我们的数据与规则下独立 reproduce。

禁止第三种：

> “README 说有效，所以我们采用。”

---

## 下一轮源码审计队列

P0：

1. `R1ch1k/betting-backtester`：取得完整 source/tests，运行 test suite，核实 anti-lookahead / bootstrap / determinism。
2. `GitSimaao/proofodds`：重点审 `ledger.py / verify.py / rescore.py / grade.py`。
3. `gcunharodrigues/sports-betting-ml-audit`：逐个检查 football experiments、threshold sweep 与多重比较计算。
4. `mberk/shin`：审核心算法 + tests，与 `penaltyblog` implied-probability 方法交叉对照。

P1：

5. `sparegk/odds-quant`：审 snapshot schema / incomplete-market rejection / signal-state implementation。
6. `betcode-org/flumine`：只审 runtime/event/risk 部分，不研究 Betfair 业务本身。
7. `mperi1208/value-bet-model`：审 calibration split、BUY-subset diagnostics 与 post-hoc 风险。

**Gate：未达到 AUDITED CORE 的仓库，不允许成为 `football-betting-research` 的直接依赖。**



## v2.1 第二批深审增补

### C1. `GitSimaao/proofodds` — 仍为 SCOUTED+，但设计优先级升至 P0

本轮进一步读了仓库公开的 ledger / verification 设计说明。它的价值不在“模型准不准”，而在**研究证据如何做到赛前可验证、赛后不可静默改写**。

确认的公开机制包括：

- `predictions/` 作为 append-only ledger；
- 每个 entry 连接前一个 entry 的 SHA-256；
- entry 记录 generator Git commit、dirty working-tree 标记、source digest；
- 预测在 kickoff 前公开；
- `verify.py` 刻意使用独立实现并只依赖标准库，用来验证 chain；
- `rescore.py` 再用另一套实现重算 de-vig、log loss、confidence interval；
- historical replay 明确写入独立目录，不冒充 live track record；
- 分组/league membership 在新组出结果前预先冻结，防止后来按结果重组样本；
- 还进一步使用 OpenTimestamps 保存外部存在时间证据。

**真正值得我们借鉴的不是 OpenTimestamps 本身，而是“双重独立验证”的设计：**

1. `verify` 只回答“历史记录有没有被改”；
2. `rescore` 只回答“这些记录的评分有没有算错”。

这两件事不能用同一套代码互相证明。

**对我们的具体决定**

未来 R8 prospective shadow ledger 建议拆成：

- `seal`：生成赛前 canonical decision record；
- `verify-ledger`：只验证 hash chain / immutability；
- `rescore`：独立读取赛前记录 + 赛果 + reference close，重新计算所有指标；
- historical replay 必须与 live ledger 使用不同目录/namespace；
- 新联赛、新信号 family、新阈值 family 的 membership 在看到结果前冻结。

**为什么仍不升级为 PARTIAL AUDIT**

目前核心 `ledger.py / verify.py / rescore.py` 尚未逐函数取得全文并交叉检查，当前证据仍主要来自仓库公开技术说明与可见结构。下一轮需要 clone 后实际篡改一条历史记录，看 verifier 是否按声明失败。

---

### C2. `gcunharodrigues/sports-betting-ml-audit` — 方法论价值高，但“总负收益结论”证据等级下调

这个仓库第一眼很容易被误读成“系统证明公开 ML 无法打败博彩市场”。

深入阅读后，作者自己披露了多个研究缺陷：

- tennis feature extraction 存在日期计算 bug；
- football v2/v3 使用 home/not-home 二分类，把 draw 合并到 negative class，可能扭曲 away edge；
- Singapore horse-racing 数据中删除了大量 impossible-overround rows；
- 没覆盖 Asian handicap 等其他结构；
- repo 当前只有 1 commit。

这意味着：

> 它对“研究为什么容易产生假阳性”的总结很有价值；  
> 它对“标准 ML 一定无法盈利”的总判断，不应被我们当成外部定论。

**仍然值得强制吸收的部分**

其多重比较案例非常具体：

- football 一次 sweep 36 个 variant；
- 少数正 ROI 与大量负结果并存；
- Bonferroni 后正结果不成立；
- 小样本高 ROI 的 standard error 极大。

这应该转化成我们实验注册规范：

1. 每次 sweep 先定义 experiment family；
2. 保留所有参数组合，不只保留 top N；
3. primary test 与 exploratory search 分离；
4. exploratory 中发现的阈值必须进新的 OOS batch 才能转 confirmatory；
5. ROI 必须附 n、cluster-aware uncertainty / CI；
6. 多重比较校正成为正式 gate，而不是论文式附注。

**项目定位**

- 作为 **methodological anti-pattern catalog：P0**
- 作为“市场不可击败”的证据：**禁止使用**
- 当前证据等级保持 `SCOUTED+`，待逐实验脚本复核。

---

### C3. `mberk/shin` — SCOUTED+，去水参考优先级提高

进一步确认：

- 79 commits；
- repository 有独立 `tests/`、CI、Rust core 与 Python wrapper；
- 实现不是黑箱只吐概率，还能返回：
  - iterations
  - delta
  - estimated insider fraction `z`
- 用户可以显式检查是否达到 convergence threshold；
- 二元 outcome 有解析特例；
- README 给出了原始 Shin / Jullien-Salanié / Štrumbelj 等学术引用。

**对我们的实际意义**

以前“去水”容易被写成一个函数：

`p_i = (1/o_i) / Σ(1/o)`

v2.1 以后建议把 `pricing/de_vig.py` 定义成可插拔方法：

- proportional
- additive
- power
- Shin

统一输出除了 probability 外，还要有：

- method
- convergence status（需要时）
- method parameters / diagnostics
- source odds hash
- implementation/version

**关键认识**

不同去水方法的结果差异是**市场建模假设差异**，而不是“哪个算法算出了真实概率”。

因此实验中比较 Sporttery vs Pinnacle 时，至少要做 de-vig sensitivity：

> 一个候选 edge 是否只在某一种去水方法下存在？

如果换 proportional / Shin / power 后 edge 符号就翻转，这类候选应降级或 BLOCKED_UNCERTAIN。

**为什么暂不升级**

本轮还未逐读 Rust/Python 核心实现与 tests，所以暂不称 `AUDITED CORE`。

---

### C4. `sparegk/odds-quant` — SCOUTED+，但数据契约设计值得直接转成我们自己的规范

本轮进一步检查了其公开的数据导入契约。几个细节与我们非常吻合：

- odds row 要有 `provider_event_key`、competition/season、kickoff、bookmaker、market、selection、decimal odds、`observed_at`；
- 可带 `source_updated_at`、settlement rule、closing flag；
- timestamp 必须带 UTC offset；
- event identity 冲突时整批拒绝；
- bookmaker snapshot 缺少该 market 应有完整 outcome set 时整批拒绝；
- corrected result 追加 superseding observation，而不是改写旧值；
- prospective snapshot 不能事后猜成 closing snapshot；
- source publication/observation time 不完整时，不假造时间。

**这与 SportteryAPI 的“尽量返回 partial market”形成很好的对照。**

我们采纳 odds-quant 这一侧的纪律：

> **数据不完整时宁可 BLOCKED，也不制造一个看起来完整的 fair probability。**

建议正式写入 canonical schema contract：

- `observed_at`：我们实际获得这条信息的时间；
- `source_updated_at`：来源声称最后更新的时间；
- `effective_at`：信息真正适用时间（如果可证）；
- `kickoff_at`；
- `settled_at`；
- `supersedes_id`；
- 所有 timestamps offset-aware。

同时规定：

- closing line 只能来自明确 closing feed/contract，禁止后推；
- corrected score 用新 observation supersede，禁止覆盖；
- incomplete market 不进入 pricing；
- identity conflict 整批 quarantine。

**证据限制**

目前这些信息来自其公开工程说明和数据契约，核心 importer 源码尚未逐函数审计，所以仍保持 SCOUTED+。

---

## v2.1 当前新增硬规则

经过第二批审查，正式增加以下研究纪律：

1. **负结果项目也要审计。**  
   “它跑出来亏钱”不自动说明它的方法正确；负结果同样可能由 bug、错误标签或错误价格造成。

2. **历史不可篡改与评分正确是两件事。**  
   future ledger 至少需要独立 `verify` 与独立 `rescore`。

3. **实验 family 必须显式登记。**  
   threshold / model / league / market 的 sweep 都属于 multiple-comparison family，不能只汇报最好结果。

4. **去水敏感性进入候选信号 QA。**  
   edge 对 proportional/Shin/power 极度敏感时，不允许直接 BUY。

5. **不完整市场 fail-closed。**  
   固定 outcome set 缺一项时，不计算去水概率和 EV。

6. **时间字段不可猜。**  
   `observed_at`、`source_updated_at`、`closing_at` 的语义必须分开；没有证据就 UNKNOWN。

7. **赛前记录只能追加，不能回写。**  
   赛后只追加 settlement / correction / supersession。

这些约束将直接进入后续 Research Charter、canonical data schema 和 backtester acceptance tests。



## v2.2 第三批深审增补

### D1. `betcode-org/flumine` — PARTIAL AUDIT

**已实际检查**

- `flumine/baseflumine.py`
- repository layout / tests / docs / examples
- 运行框架公开实现

**源码观察**

`BaseFlumine` 的确不是一个“策略脚本集合”，而是完整的运行控制层。核心实现中真实存在：

- FIFO handler queue；
- clients / streams / strategies / markets 分离；
- live execution 与 simulated execution 抽象；
- middleware；
- logging controls；
- default controls：
  - order validation
  - market validation
  - strategy exposure
- background workers；
- strategy 注册；
- stream 生命周期；
- market book event 处理；
- latency 监测。

其中一个对我们尤其有用的细节：market book 进入处理链时，会根据 publish time 计算 latency，并对明显延迟的行情做日志记录。

这说明“**数据新鲜度是运行时属性，而不是研究脚本最后才看的字段**”这一思想值得直接吸收。

**我们应该借什么**

未来 Runtime 层可以借它的职责划分：

`stream/input -> middleware -> strategy -> controls -> execution/notification -> logging`

具体到我们的竞彩系统：

- `stream/input`：竞彩/SP、sharp market、阵容/事件快照；
- `middleware`：schema、freshness、identity、完整性检查；
- `strategy`：冻结的信号规则；
- `controls`：最大场次、数据新鲜度、信息完整度、预算/暴露、禁止条件；
- `execution`：我们不是自动下注，而是生成/推送人工可执行指令；
- `logging`：每次 WATCH/CANDIDATE/BUY/PASS/BLOCKED 的事件账本。

**我们不应该借什么**

- Betfair 的 order/market/execution domain model 不应原样搬进来；
- exchange-specific partial fill、cancel/replace 等复杂度当前对中国竞彩没有必要；
- 不需要把一个成熟交易框架整体作为强依赖。

**结论**

`flumine` 的价值是**运行架构范本**，不是足球概率或 edge 来源。

当前等级：`PARTIAL AUDIT`。  
建议：借设计，不直接依赖整个框架。

---

### D2. `mperi1208/value-bet-model` — PARTIAL AUDIT，v1 结论正式修正

**已实际检查**

- 当前 README / 历史更正说明；
- `src/model.py`
- `src/backtest.py`

#### 1. 项目本身已经发生路线变化

当前作者公开区分两条线：

- **公开数据 ML**：修正后长期表现为负；
- **sharp-market anchor + line shopping**：作者当前报告为正 ROI / 正 CLV。

也就是说，仓库现在自己也从“模型比市场聪明”转向了“sharp market 作为价格锚、寻找相对错误定价”。

这与我们的路线高度相关，但必须保持证据边界：

> 作者现在报告的 sharp-anchor 正收益只是候选假设，不能当作我们已经验证的事实。

#### 2. 校准设计确实已经修正

当前 `src/model.py` 的 walk-forward split 明确形成：

- train seasons
- validation season
- test season

随后先训练 XGBoost，再使用 validation fold 进行 sigmoid / Platt calibration。

这比早期被作者自己否定的“全 OOS isotonic calibration”要干净得多。

**但一个容易被 README 掩盖的细节是：**

模型特征并非完全与赔率市场隔离，feature list 中仍包含市场相关变量，例如赔率 spread / movement 一类信号。

因此将其结果解释成“纯比赛数据独立打败 bookmaker”是不严谨的。

#### 3. threshold optimizer 是典型的“双刃工具”

当前 `backtest.py` 明确提供 edge threshold sweep：

- 从多个 threshold 扫描；
- 输出 bets / wins / ROI / profit；
- 找最优阈值。

这在 training / exploratory 阶段有价值；但如果把 test set 传进去，再选表现最好 threshold，就会立刻变成 post-hoc optimization。

**我们的规则：**

- threshold search 必须标记为 exploratory；
- sweep 产生的阈值冻结后，只能进入新的 OOS batch；
- confirmatory test 不允许再次调 threshold。

#### 4. bootstrap 粒度需要我们自己升级

该项目当前显著性函数：

- one-sample t-test on per-bet profit；
- ordinary bootstrap by resampling individual bets。

如果策略严格保证一场只有一注，这可以作为简单近似；但我们的未来系统可能同一比赛有不同 market/selection 候选，bet 之间并不独立。

所以我们的 generic backtester 必须：

- bootstrap / resample 的基本单位默认是 **fixture / match event**；
- 同一比赛里的所有下注一起抽样；
- portfolio 层另做 exposure-aware 统计。

#### 5. 作者两次公开纠错本身是高价值信息

这个项目的价值不只是算法，而是它公开保留了“结果被自己推翻”的过程。

对我们有直接教育意义：

- 漂亮收益首先当 bug suspect；
- calibration 设计可以制造伪 edge；
- CLV 计算也会因为时间/算术口径被高估；
- portfolio arithmetic 也必须独立核对；
- README 中的当前数字不代表历史数字从未变化。

**结论**

把它升级为 `PARTIAL AUDIT`。

可借：
- walk-forward train/val/test；
- 独立 calibration；
- 失败记录方式；
- sharp-anchor hypothesis。

不可直接借：
- 作者的正收益结论；
- test-set threshold optimization；
- 通用场景下逐 bet bootstrap；
- “模型独立于市场”的宽泛表述。

---

## v2.2 由第三批审计新增的工程原则

1. **Runtime controls 独立于 strategy。**  
   策略即使想 BUY，也必须经过 freshness、market completeness、budget、exposure、identity 等中央 controls。

2. **latency/freshness 在数据进入系统时判断。**  
   不能等到生成推荐后才发现输入已经过期。

3. **探索阈值与确认阈值彻底分离。**  
   threshold sweep 的输出永远不能在同一数据上升级成 confirmatory evidence。

4. **bootstrap 默认以比赛为 cluster。**  
   “一注一行”不代表这些行统计独立。

5. **README 中的“独立模型”必须检查实际 feature list。**  
   任何 market-derived feature 都要明确登记。

6. **外部项目的自我纠错记录属于正面工程信号，但不是盈利证据。**  
   愿意公开推翻旧结果说明审计文化较好；最终研究结论仍要由我们独立 reproduce。

---

## v2.2 当前优先级重新排序

### P0 — 继续源码审计 / 复现

1. `R1ch1k/betting-backtester`
   - 目标：完整取得 core source/tests；
   - 实际运行 test suite；
   - 人工构造 lookahead mutation；
   - 验证 match-bootstrap / determinism。

2. `GitSimaao/proofodds`
   - 目标：实际篡改 sealed ledger；
   - 验证 hash chain 是否失败；
   - 比较 verify / rescore 是否真正独立。

3. `mberk/shin`
   - 目标：读 Python/Rust core + tests；
   - 与 penaltyblog / proportional / power 做固定赔率交叉验证。

4. `mperi1208/value-bet-model`
   - 目标：只复现其 **sharp-anchor** 部分；
   - 特别核对 opening/closing 定义、Power de-vig、line-shopping 可获得性、时间戳和执行约束。

### P1 — 工程架构参考

5. `betcode-org/flumine`
   - Runtime/control/event 设计已足够值得借鉴；
   - 不需要复现 Betfair 交易功能。

6. `sparegk/odds-quant`
   - 下一步只审 importer / schema / signal-state source；
   - 核对 README 的 fail-closed 是否真的在代码中执行。

7. `probberechts/soccerdata`
   - 不需要证明它“永远能抓到数据”；
   - 重点提取 provider interface / cache / fixtures tests 的可复用模式。

### 继续保留但不提高优先级

- 高 accuracy 足球分类器；
- LLM/Agent 比赛 narrative；
- 自动串关优化；
- UI dashboard。

这些都必须等 canonical data / pricing / backtest / prospective ledger 通过 Gate 后再谈。



## v2.3 第四批源码审计增补

### E1. `mberk/shin` — 升级为 AUDITED CORE

**本轮已实际读取**

- `python/shin/__init__.py`（180 行）
- `tests/test_shin.py`
- repository layout / history / CI structure

**实际实现**

Python 层包含一个纯 Python fallback optimiser，并默认调用 Rust optimiser：

- 初始 `z = 0`
- 迭代 Jullien–Salanié 形式的更新式；
- `delta = |z - z0|`；
- 达到 `convergence_threshold` 或 `max_iterations` 即停止；
- 默认：
  - `max_iterations = 1000`
  - `convergence_threshold = 1e-12`
- 二元市场单独走解析公式；
- 三元及以上通过迭代估计 `z`；
- 最终概率由 `z` 与 inverse odds 计算。

输入层明确检查：

- outcome 数必须 >= 2；
- odds 必须 >= 1。

`full_output=True` 会返回：

- `implied_probabilities`
- `iterations`
- `delta`
- `z`

#### 一个重要的源码级风险：未收敛不会自动 fail

纯 Python `_optimise()` 在：

- `iterations == max_iterations`
- 且 `delta` 仍大于 threshold

时只是退出循环并返回当前 `z`。

随后 `calculate_implied_probabilities()` 仍会据此产生 implied probabilities。

如果调用者使用默认：

`full_output=False`

那么：

- `iterations`
- `delta`
- `z`

全部被丢弃。

也就是说，**调用者可能拿到一个“看起来正常”的概率向量，却不知道 optimiser 是否真正收敛。**

README 确实提醒用户用 `iterations` / `delta` 检查 convergence，但 API 本身不是 fail-closed。

#### 测试实际覆盖

`test_shin.py` 真实存在，并检查：

- 空赔率 / 单一 outcome / odds < 1 的错误；
- 经典三项 odds `[2.6, 2.4, 4.3]` 的数值结果；
- sequence 输入；
- mapping 输入；
- full output；
- 二元市场与 additive method 的等价；
- `ShinOptimisationDetails` mapping-like interface。

尤其值得注意：

测试对 `force_python_optimiser=[True, False]` 做参数化，因此相同已知样本会分别经过：

- Python optimiser；
- 默认 Rust optimiser。

至少在该 benchmark 上，两条实现路径都要满足同一数值预期。

#### 测试未明显覆盖的内容

当前单测规模并不大，尚未看到专门测试：

- 强制制造 non-convergence；
- 极端高 overround；
- 极端长赔率；
- NaN / inf；
- 赔率接近 1 的数值稳定性；
- outcome 很多时的收敛边界。

因此“有 tests”不能升级成“所有数值风险已覆盖”。

**我们的采用方式**

`shin` 可以进入 pricing layer 的正式候选 reference，但必须由我们自己的 wrapper 包住：

1. 永远调用 `full_output=True`；
2. 若 `iterations >= max_iterations` 且 `delta > threshold`：
   - 状态 = `DE_VIG_NOT_CONVERGED`
   - 禁止产生 EV / BUY；
3. 验证所有 input odds：
   - finite
   - > 1（按我们的业务契约）
   - expected outcomes complete
4. 记录：
   - method=`shin`
   - library version
   - `z`
   - iterations
   - delta
   - source odds hash
5. 用固定 golden cases 与 proportional / power / penaltyblog 实现交叉验证。

**结论**

核心 Python 实现 + tests 已足够理解其真实行为，证据等级升级为：

`AUDITED CORE`

但尚未在我们自己的环境运行，因此不是 `REPRODUCED`。

---

### E2. `GitSimaao/proofodds` — 设计审计继续加深，但暂不冒进升级

本轮公开仓库进一步确认了一些非常符合我们需求的边界纪律：

1. **sealed but unscored != evidence**
   - 项目明确区分“已经封存了概率”与“有 closing benchmark 可以评分”；
   - 没有可比较 closing line 的市场不会伪装成 edge claim。

2. **historical replay 与 live record 完全分 namespace**
   - replay 写入 `_replay/` / preview；
   - 明确说明它是 backtest，不是 track record；
   - 不允许 replay 污染 `predictions/` live ledger。

3. **group membership 先冻结**
   - 新增联赛组在出现任何 graded result 前先 commit；
   - 防止看到结果后再重组 pool 以改善 pooled score。

4. **join failure 可见而不是静默消失**
   - club name resolver ambiguous 时返回 unresolved，而不是强行挑一个；
   - entry 记录哪些联赛没能 fit；
   - raw feed name 随 sealed record 保留，之后可以通过 override 改善 grading，而不修改旧 ledger。

5. **不同盘口不可直接比较 price CLV**
   - creator sealed AH line 与 closing main line 不同，项目会显示两条线和实际 flat-stake result；
   - 但刻意不报 numeric price CLV，因为两个 handicap price 不是同一合约。

这最后一条对我们尤其重要：

> **只有“同一 selection + 同一 line + 同一 settlement rule”的价格才允许直接做 CLV price ratio / probability comparison。**

否则必须先做盘口等价转换，或者标记 `NON_COMPARABLE_LINE`。

**对我们 prospective ledger 的新增要求**

- `benchmarkable: true/false`
- `benchmark_reason`
- `selection_contract_hash`
  - market
  - selection
  - line
  - period
  - settlement rule
- closing benchmark 不同 contract 时不能直接计算 CLV。

**证据等级为什么仍暂不升**

虽然仓库技术说明非常详细，且公开目录显示 `proofodds/`、`tests/`、`predictions/`、`timestamps/` 等真实结构，但本轮仍未逐函数读到 `ledger.py` / `verify.py` / `rescore.py` 的全文。

因此继续保持 `SCOUTED+`，而不是因为文档写得好就提前给 `AUDITED CORE`。

---

### E3. `R1ch1k/betting-backtester` — 保持 PARTIAL AUDIT，不被 README 的“~800 tests”诱导升级

本轮再次确认仓库真实存在：

- `src/betting_backtester/`
- `tests/`
- `data/`
- `docs/`
- `scripts/`

README 明确描述：

- event-by-event simulation；
- match-level bootstrap；
- walk-forward；
- per-market commission；
- structural lookahead guard；
- deterministic invariant；
- regime reversal test；
- ~800 tests；
- 明确不模拟 live slippage / latency / partial fill。

这些设计都对。

但 GitHub 当前索引仍未稳定返回：

- `backtester.py`
- `reporting.py`
- `walk_forward.py`
- regime reversal test

的实际源码全文。

因此**不能因为它宣称有 800 tests 就升级为 AUDITED CORE**。

这也是本项目“证据等级”制度存在的意义：

> README 对测试数量的声明，本身不是测试通过证据，更不是我们理解了测试内容的证据。

当前仍保留为 `PARTIAL AUDIT`。

**值得马上写入我们自己设计、但不依赖它实现真假的原则仍然成立：**

- bootstrap cluster = match；
- event-order lookahead guard；
- walk-forward chained bankroll；
- rejected decision log；
- deterministic replay；
- backtest 与 live execution 明确分界。

但这些应该成为**我们的 acceptance criteria**，而不是简单 import 该库后视为完成。

---

## v2.3 新增硬规则

1. **任何 iterative de-vig 都必须显式检查 convergence。**
   library 返回概率 ≠ 算法已成功收敛。

2. **第三方默认 API 如果隐藏 diagnostics，我们必须包装。**
   研究系统优先 fail-closed，不优先“调用方便”。

3. **CLV 比较必须先证明 betting contract 相同。**
   不同 handicap line / settlement rule 的价格不能直接相除或比较。

4. **sealed prediction 与 benchmarkable prediction 分开。**
   没有同合同 closing reference 时，可以保存预测，但不能制造 edge/CLV 结论。

5. **README 的 test count 不是 evidence level。**
   只有实际读过/运行过与我们拟复用行为有关的 tests，才允许提升证据等级。



## v2.4 理论与研究框架审计

> 本节开始把“外部世界侦察”从 GitHub 源码扩展到学术与统计方法。目标不是增加背景知识，而是把成熟理论转成 `football-betting-research` 的可执行研究 Gate。

---

### F1. 博彩市场效率：必须区分“概率预测准确”与“经济可盈利”

#### 核心文献

- Hegarty & Whelan (2024), *Comparing two methods for testing the efficiency of sports betting markets*, Sports Economics Review.
- Angelini & De Angelis (2019), *Efficiency of online football betting markets*, International Journal of Forecasting.
- Franck, Verbeek & Nüesch (2010), *Prediction accuracy of different market structures — bookmakers versus a betting exchange*.
- Forrest, Goddard & Simmons (2005), *Odds-setters as forecasters: The case of English football*.
- Štrumbelj & Robnik Šikonja (2010), *Online bookmakers’ odds as forecasts: The case of European soccer leagues*.

#### 理论上的关键区分

博彩市场研究里有两个容易被混在一起的问题：

1. **统计/预测效率**：赔率转换成的概率是否与实际频率一致，能否作为高质量 forecast；
2. **经济效率**：在真实可执行赔率、佣金/税费/摩擦之后，是否仍存在正期望投注。

“有 favourite-longshot bias”并不自动等于“可以赚钱”。

已有研究多次发现：
- 赔率中可以存在系统性偏差；
- 但偏差往往不足以覆盖 bookmaker margin；
- 不同 bookmaker / market structure 的信息效率也不完全一样。

因此我们的研究不能采用：

> “发现统计显著偏差 → 直接宣布 edge”

而必须采用：

> “偏差存在 → 量化 magnitude → 加入真实执行价格/摩擦 → OOS 经济检验”。

#### 2024 年方法论文带来的直接修正

Hegarty & Whelan (2024) 比较了两种常见的效率回归：

- 直接使用 decimal odds 的倒数 `1/odds`；
- 使用先归一化、和为 1 的 market probabilities。

论文理论、真实足球/网球数据和模拟结果都指出：

> 用 `1/odds` 直接做回归会偏向“接受市场效率”，并可能低估 favourite-longshot bias。

而 normalized probability regression 更适合作为强效率检验。

**对我们的硬规则：**

R3 Market Structure Census 中：

- 禁止把 raw `1/odds` 直接当 outcome probability 做效率回归；
- efficiency regression 的默认输入必须是明确注明 de-vig method 的 normalized probabilities；
- raw inverse odds 只能保留为价格特征/描述统计；
- 同一市场至少比较 proportional / power / Shin sensitivity；
- 结果必须报告“结论是否依赖去水方法”。

---

### F2. 市场类型不能混为一个“市场真值”：1X2 与 Asian Handicap 可能具有不同信息效率

#### 核心文献

Hegarty & Whelan (2025), *Forecasting soccer matches with betting odds: A tale of two markets*, International Journal of Forecasting.

论文使用欧洲足球数据比较：

- Home / Draw / Away 市场；
- Asian Handicap 市场。

其研究发现：

- 传统 1X2 市场表现出明显 favourite-longshot bias；
- Asian Handicap odds 通过其特定映射方法得到的概率，在同一批比赛上表现得更接近有效预测；
- 论文的数据与代码有公开 replication package，期刊主编曾复现数值结果。

#### 为什么 Asian Handicap 比 1X2 更难

普通 1X2：

- 3 个互斥 outcome；
- 3 个赔率；
- 概率和为 1。

Asian Handicap：

- 表面只有双方两个 quote；
- 但可能存在：
  - full refund；
  - half refund；
  - half win / half loss；
- 实际 payoff state 不止两个。

因此两个 AH price 并不能简单地按：

`1/o1, 1/o2 -> normalize`

就唯一反推出比赛状态概率。

论文专门需要对 refund probability 建模，才能从价格映射到概率。

#### 对我们的项目修正

以后禁止写笼统变量：

`p_market`

必须变成至少：

- `p_market_1x2`
- `p_market_ah`
- `p_market_ou`

并保存：

- market type
- line
- settlement contract
- de-vig / probability mapping method
- source
- timestamp

**Pinnacle/锐盘不是一个抽象真值源。**
应研究：

> 哪个 bookmaker × 哪个 market × 哪个 time horizon 是更强 baseline。

这是 R3 必须先做的 census，而不是架构里提前写死。

---

### F3. Asian Handicap 的复杂结算本身可能产生可预测的价格结构

Hegarty & Whelan (2024), *Returns on complex bets: evidence from Asian Handicap betting on soccer* 报告：

- 无退款可能的 AH bet；
- half-refund；
- full-refund

在平均 bettor loss 上存在系统性差异，而且部分差异可以从 quote 本身预测。

作者解释之一是 bettors 对复杂 refund payoff 的期望收益计算不充分。

**对我们的意义不是“照着下注”，而是提出一个正式研究问题：**

> 竞彩的让球/过关结构中，是否也存在因为 payoff complexity、展示方式、固定规则造成的系统价格偏差？

这属于 **market microstructure / product-design edge**，
和“谁会赢球”是两类完全不同的研究。

因此未来 Edge Research 至少分：

- `E-FUNDAMENTAL`：比赛信息；
- `E-MARKET`：不同市场之间价格错位；
- `E-PRODUCT`：结算/玩法/展示结构造成的价格偏差。

三类不能混在一个模型中后再事后解释。

---

### F4. 概率预测的第一评价标准不是命中率，而是 Proper Scoring Rules

#### 核心理论

Gneiting & Raftery (2007), *Strictly Proper Scoring Rules, Prediction, and Estimation*：

proper scoring rule 的核心性质是：
如果预测者真实相信某个概率分布，诚实报告该分布在期望上最优。

常用：

- Log score / log loss
- Brier / quadratic score

这非常适合我们的目标，因为系统需要的是：

> 0.55 到底是不是一个可信的 0.55

而不是：

> 预测胜负猜对了多少场。

#### 项目规则

模型评价 primary metrics：

1. **Log Loss**
2. **Brier Score**
3. **Calibration diagnostics**

ROI / CLV 是经济结果，不替代 forecast-quality metrics。

Accuracy：
- 只作为易理解的 secondary descriptive metric；
- 不允许用于模型主排序。

---

### F5. Calibration 与 Sharpness：我们真正想要的是“先校准，再有区分度”

Gneiting, Balabdaoui & Raftery (2007) 提出经典范式：

> maximize sharpness subject to calibration

简化到我们的足球概率：

- **Calibration**：报 60% 的比赛，长期大约 60% 发生；
- **Sharpness**：不要所有比赛都懒惰地报 33/33/33；真正有信息时能把概率推离 base rate。

一个模型可以：
- 很“自信”（sharp）；
- 但完全错位（uncalibrated）。

这样的模型特别容易产生“高 EV 假象”。

#### Brier decomposition

Murphy (1973) 把 Brier score 分为：

- reliability
- resolution
- uncertainty

这给我们一个非常合适的模型诊断语言：

- reliability：概率有没有说准；
- resolution：有没有把容易/困难的比赛区分出来；
- uncertainty：样本本身不可避免的不确定度。

**未来模型报告必须至少包含：**

- overall calibration；
- reliability diagram；
- Brier / log loss；
- BUY-subset calibration；
- probability-bin sample size；
- market-baseline relative skill。

不能只发一个 ROI。

---

### F6. BUY / PASS 应当采用 Selective Prediction / Risk–Coverage 的思想

机器学习里存在成熟的 **selective classification / reject option** 框架：

模型可以选择不预测，从而在：

- coverage
- risk

之间做显式权衡。

这和我们的竞彩系统非常接近：

- 所有比赛 = universe；
- 通过数据/价格/置信门槛的比赛 = coverage；
- BUY 是更小的 selective subset；
- PASS 不是失败，而是策略的一部分。

#### 我们不直接照搬分类误差 risk

博彩里的 risk 不只是 error rate。

建议我们的 `coverage curve` 记录：

x 轴：
- 被系统允许进入 CANDIDATE/BUY 的比例

y 轴同时看：
- log loss
- calibration error
- market-relative probability error
- CLV
- ROI
- sample count / uncertainty

**重要 sanity check：**

理论上，如果 selector 真能识别“更可靠/更有 edge”的样本，
随着覆盖率降低、门槛提高，至少一部分质量指标应改善。

如果出现：

> edge threshold 越高，BUY subset 反而校准越差、CLV 越差

这通常说明 selector 在挑模型最自信的错误。

---

### F7. Backtest overfitting：一次 OOS 不是免死金牌

#### 核心文献

- White (2000), *A Reality Check for Data Snooping*
- Hansen (2005), *A Test for Superior Predictive Ability*
- Bailey et al. (2015), *The Probability of Backtest Overfitting*
- Bailey & López de Prado (2014), *The Deflated Sharpe Ratio*
- Sullivan, Timmermann & White (1999), data-snooping / technical trading rules

这些金融文献不应机械套进足球，但它们揭示的研究问题与我们完全一致：

> 如果尝试了很多 league / market / threshold / feature / model / window，然后只报告最好一个，普通 p-value、ROI、甚至单一 holdout 都可能严重乐观。

Bailey 等强调：
试验配置越多，历史上“看起来特别好”的最优策略越容易只是选择偏差。

#### 我们采用什么，不采用什么

**采用：**

- experiment family registry；
- trial count；
- exploratory / confirmatory 分离；
- bootstrap family-level test；
- White Reality Check / Hansen SPA 作为候选统计工具；
- 新 OOS batch 再确认；
- 全部失败配置保留。

**不机械采用：**

- 不直接把 Deflated Sharpe Ratio 当足球下注的主统计量；
- 稀疏、离散、同场相关的 bet return 不完全符合传统资产收益序列。

我们更适合：

- fixture-cluster bootstrap；
- family-level multiple-testing correction；
- prospective batch replication。

---

### F8. 新增“试验家族”概念：所有参数搜索都有成本

以后每个实验必须登记：

- `experiment_id`
- `family_id`
- hypothesis
- primary metric
- all tried configs
- threshold grid
- leagues
- markets
- feature families
- model families
- tuning data
- confirmatory data
- stop rule

比如：

`EV threshold = 1%, 2%, 3%, 4%, 5%`

不是 5 个互不相关实验，而是：

> 一个 family 里尝试了 5 个候选。

如果最后只报告 3% 最漂亮：
- 必须把另外 4 个结果一起保留；
- 3% 只能算 exploratory winner；
- 下一批冻结数据才能确认。

这是针对我们旧研究历史最重要的制度升级之一。

---

### F9. Closing line / CLV：重要，但不是“盈利证明”

多项体育市场研究发现：

- closing line 往往比 opening line 包含更多信息；
- 随着更多参与者和信息进入市场，价格常向更准确方向移动；
- 某些市场 closing line 的偏差会明显减少。

例如：
- NFL intra-week line 研究发现信息含量从早期 line 向 closing line 增加；
- NBA player absence 研究发现 opening line 有偏差，而 game-time line 消化了大部分信息；
- football bookmaker 文献普遍显示市场价格本身是很强的 forecast baseline。

但同时也有研究发现：
- closing price 并非所有市场、所有 bookmaker 都完全有效；
- bookmaker 间仍存在信息差；
- 1X2 等市场存在 favourite-longshot bias；
- opening/market structure 本身仍可能提供增量信息。

因此：

> **CLV 是“是否早于市场获得/处理信息”的强诊断指标，不能当成最终盈利证明。**

我们的正式定义：

- `CLV_same_contract`：同一 market / selection / line / settlement 的可比 closing price；
- `CLV_equivalent_contract`：经过正式盘口等价映射；
- `CLV_unavailable`：无法证明同合同可比时。

禁止不同 handicap line 的两个 price 直接计算 CLV。

---

### F10. Market baseline 不能只选一个 bookmaker

已有研究发现：
- individual bookmaker 的 forecast quality 有差异；
- exchange / sharp bookmaker 可能比普通 bookmaker 更准；
- bookmaker 有时没有充分利用竞争者价格里的信息；
- best-price / market consensus 与单一 bookmaker 的经济表现不同。

因此未来 R3 不是：

> “Pinnacle = 真值”

而是测试候选 baseline：

- sharp bookmaker A
- sharp/market consensus
- median
- best available price
- exchange（如数据可得）
- Asian Handicap-derived baseline
- 1X2 de-vig baseline

最终确定的是：

> **reference market policy**

而不是宗教式指定一家 bookmaker。

---

### F11. Kelly sizing 暂时后置，而且必须考虑概率估计误差

Kelly criterion 在“真实概率已知”时有清晰的 log-growth 最优性质。

但我们的现实恰好相反：

> 最不确定的东西就是 p。

理论与实践文献长期讨论：

- full Kelly 波动/回撤很大；
- fractional Kelly 可以牺牲一部分期望增长换取更低风险；
- 参数不确定性应降低仓位。

因此项目顺序明确：

1. 先证明 probability / price edge；
2. 再证明 prospective persistence；
3. 最后才讨论 sizing。

**早期 shadow / 小额实盘不允许让 Kelly 把一个脆弱的概率差异放大成大额下注。**

---

### F12. 由理论研究形成的正式研究 Gate

#### Gate M0 — Data contract

必须通过：

- outcome completeness；
- fixture identity；
- timestamps；
- provenance；
- append-only raw snapshot；
- parser version；
- no silent schema drift。

失败：不进入 pricing。

#### Gate M1 — Pricing validity

必须通过：

- settlement contract；
- de-vig convergence；
- de-vig sensitivity；
- same-contract comparability；
- margin sanity。

失败：不生成 EV。

#### Gate M2 — Forecast quality

候选模型必须相对 market baseline：

- log loss 有增量；
- Brier 有增量或至少不恶化；
- calibration 不恶化；
- BUY subset 不出现明显过度自信；
- sample size 足够。

失败：不进入 value strategy。

#### Gate M3 — Market/economic test

必须区分：

- statistical bias；
- executable economic edge。

加入：
- 竞彩真实 SP；
- 税费/规则/不可买市场；
- execution cutoff；
- line availability；
- stake limits/rounding（如适用）。

失败：不进入 backtest candidate。

#### Gate M4 — Multiple-testing / overfit audit

必须登记：

- experiment family；
- trial count；
- all configurations；
- correction / family bootstrap；
- frozen threshold。

只在同一批数据上“挑出最好参数”：
- 只能标 exploratory。

#### Gate M5 — Walk-forward / OOS

必须：

- expanding/rolling chronological；
- training/calibration/test 分离；
- feature as-of；
- fixture-cluster uncertainty；
- deterministic rerun。

失败：不进入 shadow。

#### Gate M6 — Prospective shadow

必须：

- pre-match sealed record；
- BUY/PASS 都记录；
- hash chain；
- independent rescore；
- CLV same-contract；
- no historical rewrite。

只有 prospective batch 支持时才进入小额真钱。

---

## v2.4 最重要的项目路线变化

经过开源项目 + 理论文献两条线交叉后，项目研究对象进一步明确：

### 以前容易问

> “我们能不能预测准比赛？”

### 现在应问

> “在一个已经非常强的市场概率 baseline 之上，是否存在某种**赛前可观察、可复现、可执行**的信息，使我们对中国竞彩的某个具体投注合同形成稳定的 market-relative edge？”

这四个限定词缺一不可：

- **赛前可观察**
- **可复现**
- **可执行**
- **market-relative**

这比“做一个更准的足球模型”窄得多，但也科学得多。

---

## v2.4 建议的最终研究指标体系

### Forecast 层（primary）

- Log Loss
- Brier Score
- Calibration / reliability
- Resolution
- Market-relative skill

### Selection 层

- Coverage
- BUY-subset calibration
- Edge-bin monotonicity
- Rejection/blocked reason distribution

### Market 层

- de-vig sensitivity
- bookmaker/market baseline comparison
- opening → decision → closing movement
- same-contract CLV

### Economic 层

- ROI
- average EV at decision
- drawdown
- hit rate（secondary）
- turnover
- executable availability

### Statistical integrity

- n matches
- n bets
- effective/clustered sample size
- fixture-cluster bootstrap CI
- experiment-family size
- multiple-testing status
- prospective vs historical flag

任何结果表如果没有这些上下文，禁止只报：

> “ROI +X%”。

---

## v2.4 理论来源（本轮）

- Gneiting, T. & Raftery, A. E. (2007). *Strictly Proper Scoring Rules, Prediction, and Estimation*. JASA 102, 359–378. DOI: 10.1198/016214506000001437.
- Gneiting, T., Balabdaoui, F. & Raftery, A. E. (2007). *Probabilistic forecasts, calibration and sharpness*. JRSS-B 69, 243–268. DOI: 10.1111/j.1467-9868.2007.00587.x.
- Murphy, A. H. (1973). *A New Vector Partition of the Probability Score*. Journal of Applied Meteorology 12, 595–600.
- White, H. (2000). *A Reality Check for Data Snooping*. Econometrica 68, 1097–1126.
- Hansen, P. R. (2005). *A Test for Superior Predictive Ability*. Journal of Business & Economic Statistics 23, 365–380.
- Bailey, D. H., Borwein, J., López de Prado, M. & Zhu, Q. J. (2015). *The Probability of Backtest Overfitting*. Journal of Computational Finance.
- Bailey, D. H. & López de Prado, M. (2014). *The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality*. Journal of Portfolio Management.
- Hegarty, T. & Whelan, K. (2024). *Comparing two methods for testing the efficiency of sports betting markets*. Sports Economics Review 8, 100042.
- Hegarty, T. & Whelan, K. (2025). *Forecasting soccer matches with betting odds: A tale of two markets*. International Journal of Forecasting 41(2), 803–820.
- Hegarty, T. & Whelan, K. (2024). *Returns on complex bets: evidence from Asian Handicap betting on soccer*. Review of Behavioral Finance 16(5), 904–924.
- Štrumbelj, E. & Robnik Šikonja, M. (2010). *Online bookmakers’ odds as forecasts: The case of European soccer leagues*. International Journal of Forecasting 26, 482–488.
- Forrest, D., Goddard, J. & Simmons, R. (2005). *Odds-setters as forecasters: The case of English football*. International Journal of Forecasting 21, 551–564.
- Angelini, G. & De Angelis, L. (2019). *Efficiency of online football betting markets*. International Journal of Forecasting 35, 712–721.
- Geifman, Y. & El-Yaniv, R. (2017). *Selective Classification for Deep Neural Networks*. arXiv:1705.08500.
- MacLean, L., Thorp, E. O. & Ziemba, W. T. (2011). *The Kelly Capital Growth Investment Criterion: Theory and Practice*.



## v2.5 EDGE_SPACE_MAP：从 EV 基本式反推研究路线，而不是从模型列表出发

> 目的：回答“我们是不是只是在沿已有研究继续造模型，还是已经从更底层接近穷举所有可能 edge 来源？”  
> 本节给出第一版 **路线空间穷举框架**。它不是数学意义上证明所有现实机会都已穷尽，但它试图从投注合同的期望值原语出发，把所有可行路线压缩到少数根类别，再把历史研究逐项映射进去。

---

### G1. 从基本式出发：正 EV 到底可能从哪里来？

对一个最简单的二元投注：

`EV = p * O - 1`

其中：

- `p` = 真实获胜概率；
- `O` = 实际可执行 decimal odds。

更一般地，对多状态投注合同：

`EV = Σ q_s * R_s - 1`

其中：

- `q_s` = 状态 `s` 的真实概率；
- `R_s` = 在状态 `s` 下该投注合同的实际结算回报。

因此，想让负 EV 变成正 EV，本质上只能改变以下几样东西之一：

1. **你对 `q` 的估计更准确**；
2. **你获得的价格 / payout `R` 更好**；
3. **市场对合同状态与 payout 的映射定错**；
4. **你比别人更早/更好地获得相同信息或价格**；
5. **存在合同外补贴、返还、bonus、机械错误或真正 arbitrage**。

如果一个方法没有改变以上任何一项，它就不是新的 edge 来源。

例如：

- Poisson / Bayes / XGBoost / LLM：都属于 **概率信息优势**；
- Pinnacle vs 竞彩：属于 **跨市场价格错位**；
- 盘口移动：属于 **时间/执行优势**；
- 亚洲盘 quarter-line / 串关相关性：属于 **合同/产品定价**；
- Kelly：只是 **资本分配**，本身不能制造正 EV；
- ensemble：只是概率估计器的实现方式，不是独立 edge；
- “换个更复杂模型”：如果输入信息集合没增加，仍属于同一个根类别。

---

### G2. 根级 Edge Taxonomy

基于上面的期望值原语，竞彩足球的潜在 edge 可以压缩为六个根类。

#### ROOT-A — INFORMATION EDGE / 概率信息优势

核心问题：

> 我们是否能在下注截止前，对比赛真实状态概率 `q` 给出比市场更准确的估计？

子路线包括：

A1. 历史比赛结构：
- Elo / rating
- Poisson / Dixon-Coles
- xG
- team strength
- shot / possession / event data

A2. 阵容与球员：
- 首发
- 伤停
- 门将
- 关键球员缺席
- roster depth

A3. 赛程与状态：
- travel
- rest days
- congestion
- continental competition
- rotation
- promotion/relegation incentives

A4. 环境：
- weather
- pitch
- altitude
- referee
- venue
- neutral ground

A5. 文本/公开信息处理：
- news
- coach comments
- official announcements
- social media
- LLM/Agent information extraction

A6. 小众联赛/覆盖不足：
- bookmaker 信息收集更弱的赛事
- 数据稀缺但可能更低效的市场

**关键认识：**
所有“再造一个更好预测模型”的研究都属于 ROOT-A，不能因为算法名字不同就被当作新路线。

---

#### ROOT-B — MARKET PRICING EDGE / 市场间错误定价

核心问题：

> 即使大家对比赛概率的认识差不多，竞彩给出的价格是否相对更高效市场存在可执行错位？

子路线：

B1. 竞彩 vs sharp bookmaker  
B2. 竞彩 vs betting exchange  
B3. 竞彩 vs market consensus  
B4. 1X2 vs Asian Handicap  
B5. 1X2 vs O/U / score-derived probability  
B6. bookmaker-to-bookmaker disagreement  
B7. opening vs decision-time vs closing  
B8. bookmaker-specific price shading  
B9. favourite-longshot / popularity bias  
B10. home/fan/national-team behavioural bias

ROOT-B 不要求我们“预测比赛比市场强”。

它只要求：

> 能可靠识别“竞彩这一个价格相对更强 reference market 定错了”。

这是与 ROOT-A 本质不同的一条主干。

---

#### ROOT-C — PRODUCT / CONTRACT EDGE / 产品与结算结构优势

核心问题：

> 概率可能没有被错估，但某个具体投注产品的 payout mapping 是否定错？

子路线：

C1. 亚洲盘 quarter-line：
- half win
- half loss
- refund probability

C2. 让球胜平负与 AH 的映射

C3. 比分 / 总进球 / 半全场之间的结构一致性

C4. parlay / M串N 的相关性定价

C5. 同场/跨场组合是否错误假设独立

C6. 竞彩奖金公式、舍入、固定倍数等离散规则

C7. 单关 vs 过关产品差异

C8. product complexity 导致 bettor / bookmaker 定价偏差

**重要限制：**

串关优化本身不是 edge。

只有当：
- 组合 payout 没有正确反映 joint probability；
- 或产品规则引入非线性优势；

它才进入 ROOT-C。

否则把多个负 EV 单注乘在一起通常只会放大 house edge。

---

#### ROOT-D — TIMING / EXECUTION EDGE / 时间与执行优势

核心问题：

> 我们是否能以别人拿不到或来不及拿到的价格执行？

子路线：

D1. 竞彩调整慢于 sharp market  
D2. lineup/news 出现后的短暂 lag  
D3. 竞彩 SP 固定/更新机制形成窗口  
D4. opening price 比 closing price 更可利用  
D5. line shopping  
D6. latency / stale odds  
D7. 可买性 / 截止时间差  
D8. 数据采集速度和稳定性

ROOT-D 可以没有新的比赛预测模型。

真正的优势可能只是：

> 市场已经知道，但竞彩还没完全反映。

---

#### ROOT-E — SEGMENTATION / CONDITIONAL MISPRICING / 条件性市场偏差

这是 ROOT-A/B 的横截面条件化形式，但单独列出是为了研究纪律。

核心问题：

> 全市场负 EV，但是否存在一个事前可定义、足够大的条件子集仍为正 EV？

例如：

- 某联赛
- 某赔率区间
- 某让球档
- 某赛程状态
- 某球队类别
- favourite / longshot
- 主客场
- 特定 market phase

这里是最容易 data mine 的区域。

因此 ROOT-E 默认高危：

- 必须 pre-register；
- 必须把所有筛选 family 计入 multiple testing；
- 必须新 OOS / prospective replication。

不能因为一个历史子组盈利就自动认定 edge。

---

#### ROOT-F — EXTERNAL / MECHANICAL EDGE / 外部补贴与机械异常

包括：

F1. bonus / rebate / subsidy  
F2. 真正跨市场 arbitrage  
F3. 错价 / stale quote / data error  
F4. 规则执行错误  
F5. 平台/渠道特殊优惠  
F6. 极端 rare operational anomaly

这类机会可能是真正正 EV，但：

- 往往容量小；
- 不稳定；
- 不属于“足球预测能力”；
- 可能不可长期系统化。

对中国官方竞彩而言，很多海外 sportsbook bonus 路线并不适用，应按实际规则单独确认。

---

### G3. 明确不是独立 Edge 来源的东西

以下经常被包装成“新策略”，但从基本式看并不是新的 edge 来源：

| 方法 | 为什么不是独立 edge |
|---|---|
| Kelly / fractional Kelly | 只改变仓位，不改变单注期望 |
| bankroll optimization | 只改变资本路径 |
| ensemble | 仍是 ROOT-A 的概率估计 |
| Bayesian model | 仍是 ROOT-A |
| neural network / XGBoost | 仍是 ROOT-A |
| LLM / multi-agent | 如果只是处理公开信息，仍是 ROOT-A/D |
| bet count optimization | 不改变价格与概率 |
| 选“最有信心”比赛 | 属于 ROOT-E，且容易 selection bias |
| 串关 | 除非 joint payout 错，否则属于产品包装，不自动产生 edge |
| 多联赛扩张 | 只是扩大样本 universe |
| 更漂亮 UI / agent workflow | 工程能力，不是 edge |

这张表非常重要，因为它可以避免我们把“技术复杂度增加”误认为“研究空间增加”。

---

### G4. 旧研究映射：当前仅作 PROVISIONAL，不作为最终审计结论

> 注意：以下状态来自目前已冻结 inventory 的摘要、已知旧研究结论和 Owner 提醒。  
> 旧资产正在由 WorkBuddy 集中到本地 staging。  
> 在真实文件、脚本、数据和报告逐项复核前，状态只标 `PROVISIONAL`。

状态定义：

- `KILLED`：已有较强结构证据表明路线不足以覆盖竞彩摩擦；
- `DOMINATED`：不是严格不可能，但已有更强 baseline，继续投入性价比低；
- `SURVIVES`：仍有明确研究空间；
- `UNKNOWN`：证据不足；
- `UNTESTED`：目前没有看到系统测试；
- `REVALIDATE`：旧研究做过，但受 bug / lineage / 时间问题影响，需要重验。

#### 初步路线图

| 路线 | 当前 provisional 状态 | 当前理由 |
|---|---|---|
| 通用 Poisson / 基础比赛模型直接打竞彩 | `DOMINATED` | 旧研究与外部文献均显示 market baseline 强；竞彩高抽水使小预测增量难转经济 edge |
| 更复杂 Bayes / ML 直接预测胜负 | `DOMINATED / REVALIDATE` | 算法变化不构成新 edge 来源；旧研究已广泛探索，漂亮结果曾被 bug 推翻 |
| 公开数据 feature engineering | `REVALIDATE` | 可能改善概率，但关键问题是能否覆盖 C，不是是否有统计增量 |
| 阵容/伤停/天气/赛程公开信息 | `UNKNOWN` | 属 ROOT-A/D；理论可能有短时信息优势，但需严格 as-of 与市场吸收速度研究 |
| sharp market vs 竞彩价格错位 | `SURVIVES` | 不要求我们预测比赛胜负更强；属于不同根路线 |
| Pinnacle/竞彩静态价差 | `REVALIDATE` | 旧研究做过多轮；需要基于同合同、时间同步、正确 de-vig 重新审计 |
| 1X2 vs Asian Handicap cross-market mapping | `SURVIVES` | 理论文献表明市场效率可能不同；旧研究是否真正穷尽需审计 |
| opening → closing / 竞彩调价滞后 | `SURVIVES` | 属时间优势，需高频 snapshot 才能回答 |
| favourite-longshot / popularity bias | `UNKNOWN` | 文献广泛存在统计偏差，但能否覆盖竞彩高抽水未知 |
| home/fan/national bias | `UNKNOWN` | 行为偏差可能存在，不等于经济可利用 |
| 某联赛/赔率区间/球队条件筛选 | `HIGH-RISK UNKNOWN` | 最容易 data snooping；只有预注册 + 新 OOS 才能保留 |
| Oracle 上界 / 信息上界分解 | `KEEP / CORE METHOD` | 它不是策略，而是最快判断“这条路线值不值得继续”的工具 |
| 串关作为单纯放大利润工具 | `KILLED AS EDGE SOURCE` | 若每腿负 EV，组合本身不会创造 edge，且高 hold 往往累积 |
| 串关/组合相关性定价错误 | `UNTESTED / SURVIVES` | 与普通串关不同，属于 ROOT-C joint-pricing 问题 |
| 竞彩产品规则 / 舍入 / 退款结构 | `UNTESTED / UNKNOWN` | 属 ROOT-C；需要按官方结算规则结构性枚举 |
| line shopping | `LIMITED EXECUTABILITY` | 对只在中国竞彩执行的系统不能直接跨 book 下单，但可作为 reference/price-quality 分析 |
| bookmaker/exchange arbitrage | `OUTSIDE CORE EXECUTION` | 如果最终执行只允许竞彩，则不能作为主盈利路线 |
| stale/error quote 异常捕捉 | `UNKNOWN` | 理论存在，但容量/频率可能很低 |
| Kelly / 资金管理 | `NOT AN EDGE` | 只有 edge 已存在后才讨论 |
| LLM/Agent 比赛分析 | `NOT A NEW ROOT` | 只是公开信息处理方式；必须证明相对市场有增量 |

---

### G5. 高抽水为什么必须成为“路线空间第一道筛选器”

旧研究最重要的经验之一，不是某个模型失败，而是：

> **竞彩的高摩擦 C 使大量“统计上有一点预测增量”的路线在经济上直接死亡。**

因此未来不再按：

`先做复杂模型 -> 再看 ROI`

而改成：

`先估路线可实现上界 -> 再决定值不值得建模`

对每个 ROOT / 子路线，先估：

- `C` = 竞彩执行摩擦 / margin / product cost
- `A` = opportunity availability
- `N_eff` = 有效独立样本量
- `B` = 无优势 baseline
- `U_oracle` = 完美信息/理论上界
- `U_achievable` = 公开可获得信息下的现实上界

#### 结构性停止规则

若：

`U_oracle <= C`

则该路线可以直接：

`KILLED`

不需要做任何模型。

若：

`U_oracle > C` 但 `U_achievable << C`

则：

`DOMINATED`

除非出现新的信息源或执行条件。

只有：

`U_achievable plausibly > C`

才进入后面的：

`M0 -> M6`

这把原来的研究质量 Gate 放到了正确的位置：

`EDGE_SPACE -> STRUCTURAL UPPER BOUND -> SURVIVORS -> M0–M6`

而不是：

`M0–M6 -> 不断尝试模型 -> 看有没有一个幸运结果`

---

### G6. 近似“穷举”的定义

我们不声称可以穷尽现实世界所有未来机会。

我们要穷举的是：

> **所有能改变投注期望值原语的机制类型。**

也就是：

1. 改变对真实概率 `q` 的认识；
2. 改变可执行价格 / payout；
3. 发现合同映射错误；
4. 获得时点/渠道执行优势；
5. 找到稳定条件性错价；
6. 获得合同外 subsidy / arbitrage / mechanical anomaly。

任何新策略提案必须回答：

> “它属于哪一个 ROOT？它到底改变 EV 基本式中的哪一项？”

如果回答不了，就默认：

`NOT A NEW EDGE ROUTE`

这样可以有效阻止“换模型名字重新研究同一个问题”。

---

### G7. 下一步：真正建立 Edge Exhaustion Matrix

旧资产 staging 完成后，由 ChatGPT 而不是 WorkBuddy 做：

`EDGE_EXHAUSTION_MATRIX.md`

每一条路线至少记录：

- `edge_route_id`
- root category
- mechanism
- theoretical rationale
- required data
- required timing
- execution contract
- legacy experiments
- legacy evidence path
- known bugs affecting evidence
- `C`
- `A`
- `N_eff`
- `B`
- `U_oracle`
- `U_achievable`
- external literature
- current state
- kill criterion
- reopen criterion

状态只能是：

- `KILLED`
- `DOMINATED`
- `SURVIVES`
- `UNKNOWN`
- `UNTESTED`
- `REVALIDATE`

#### reopen rule

被 KILLED/DOMINATED 的路线只有在出现以下情况时才能重开：

- 新数据源；
- 新市场结构；
- 新执行价格；
- 新结算规则；
- 新的可信 evidence 推翻原上界；
- 旧结论被确认存在重大 bug。

“换成更复杂模型”本身不是 reopen reason。

---

### G8. 外部研究对 Edge Space Map 的补充证据

本轮新增的外部研究进一步支持以下几点：

1. **Favourite-longshot bias 是长期存在的定价现象，但统计偏差不等于可覆盖 margin 的经济 edge。**
2. **市场结构本身可以制造 favourite-longshot bias，不必假设 bettor 单纯非理性。**
3. **home/local-team bias 可明显影响投注行为，但并不自动带来超额表现。**
4. **bookmaker 与 exchange、不同市场之间可能存在不同的 price formation 与效率。**
5. **parlay / joint contract 的相关性定价是一个独立问题，不能用单腿概率乘积简单替代。**
6. **2026 年预测市场研究仍观察到 product-type 与 time-to-expiry 相关的系统定价偏差，说明“产品结构/时间结构”是独立于基础胜率预测的研究轴。**

这些证据支持保留 ROOT-B / ROOT-C / ROOT-D，
同时进一步降低“只做更复杂比赛预测模型”在总研究预算中的优先级。

---

### G9. 当前路线优先级（在旧资产正式审计前）

#### P0 — 必须先审清是否仍有空间

1. `B` 市场间错价
2. `C` 产品/合同定价
3. `D` 时间/执行滞后
4. Oracle / structural upper-bound framework

#### P1 — 有条件保留

5. `A2/A3/A5` 阵容、赛程、公开事件的快速处理
6. `E` 预注册条件子集
7. behavioural bias 是否足以覆盖竞彩 margin

#### P2 — 默认降级

8. generic Poisson/Bayes/ML replacement
9. 再造新的“综合实力模型”
10. LLM 多 Agent 专家投票
11. 参数继续微调

这不是说 P2 永远无价值。

而是：

> 在证明 ROOT-B/C/D 没有更直接的结构机会之前，不应该把主要资源再次投入 ROOT-A 的模型竞赛。



## v2.6 EDGE_SPACE_MAP 外部压力测试：有没有漏掉新的根级机制？

> 目的：不是继续“找策略”，而是主动寻找能够推翻 v2.5 六根分类的反例。  
> 本轮检查近期 bookmaker market-structure、行为偏差、parlay/joint contract、price shading、prediction market 研究。结果：暂未发现必须新增第七个根级 edge 来源的机制；新文献均可映射回 ROOT-A~F。但现有 ROOT 的内部定义需要进一步收紧。

---

### H1. 更底层的数学原语其实只有四个，A–F 是工程化展开

对任意投注合同：

`EV = Σ q_s * R_s - 1`

若考虑是否能实际拿到该价格/合同，还要再乘上 execution/access 条件；若有 bonus/rebate，则加入额外外部项。

因此从最底层看，正 EV 只能来自：

1. **Belief / probability edge**  
   对 `q_s` 的估计更接近真实分布。

2. **Price / payoff edge**  
   市场给出的 `R_s` 相对真实概率过高，或合同 payoff mapping 定错。

3. **Access / timing edge**  
   你能在特定时间、渠道、额度下拿到别人或未来拿不到的 `R_s`。

4. **External subsidy / mechanical edge**  
   bonus、rebate、arbitrage、系统错价、规则错误等额外收益来源。

v2.5 的六根是为了工程研究方便：

- ROOT-A ≈ 1
- ROOT-B/C/E ≈ 2 的不同成因
- ROOT-D ≈ 3
- ROOT-F ≈ 4

因此，如果未来出现一个所谓“新策略”，它必须说明究竟改变了这四个原语中的哪一个。

---

### H2. 一个重要的“组合不能救负 EV”结论

设在当前可用信息集合 `F` 下，所有可执行基础投注合同 `i` 都满足：

`E[R_i | F] <= 1`

若策略只允许：

- 非负 stake；
- 不存在 bonus/rebate；
- 不存在额外非线性 payout；
- 不改变实际可执行价格；
- 不加入新的信息；

那么任意线性资金组合：

`Σ w_i R_i, w_i >= 0`

其条件期望仍不会凭空变成正值。

因此以下东西不能作为“被高抽水杀死以后再救活策略”的手段：

- Kelly；
- fractional Kelly；
- bankroll sizing；
- 下注数量优化；
- portfolio diversification；
- “只挑最有信心的几场”——除非选择器真的带来新的条件信息；
- 把多个独立负 EV 单注做普通乘法串关。

#### 例外

如果产品本身引入新的非线性 payout：

- parlay payout 没有正确反映 joint probability；
- correlated legs 被当成独立；
- bonus/boost；
- refund/insurance；
- rounding/subsidy；

那就不是“组合优化”，而是 ROOT-C/F 的新合同 edge。

这条区分以后必须写进 Research Charter。

---

### H3. Bookmaker margin / overround 不一定等于“真实利润率”

2025/2026 的 market-structure 研究给出一个重要修正：

在不完全竞争、bettor beliefs 存在分歧时，bookmaker 可以因为不同 outcome 的需求弹性不同而形成 favourite-longshot bias。此时：

- observed overround 仍可计算；
- 但“按比例把 overround 去掉”未必能恢复真实概率；
- overround 也未必等于各 outcome 上 bookmaker 的真实 expected profit margin。

这直接削弱了一个常见隐含假设：

> bookmaker odds = true probability × 一个简单统一 margin

因此我们的 pricing layer 不能把 proportional normalization 当作自然真值。

**新增规则：**

- `overround` 只是观测到的 quote geometry；
- `proportional_no_vig` 只是一个 market-probability estimator；
- Shin/power/additive 等也是不同结构假设；
- market efficiency 研究要做 de-vig/model sensitivity；
- 不允许从“sum(1/o)”直接推断 bookmaker 对每个 outcome 的真实成本或利润率。

---

### H4. Behavioural bias 必须拆成“偏好”与“价格 shading”

2026 年 Dmochowski 的 profit-bias identity 提醒：

> public lean 本身不够；只有 bookmaker 的 price shading 与 public lean 同时存在，偏好才会进入 bookmaker profit channel。

换句话说：

- bettors 喜欢主队；
- bettors 喜欢强队；
- bettors 喜欢 longshot；

都不能自动变成交易信号。

我们至少需要区分：

1. `DEMAND_BIAS`
   - 投注人群偏好什么？

2. `PRICE_SHADING`
   - bookmaker 是否真的因为这种需求把赔率往不利方向调？

3. `ECONOMIC_RESIDUAL`
   - 调整幅度是否大到覆盖竞彩 hold / execution cost？

#### 对 ROOT-E 的硬化

未来任何“行为偏差策略”必须证明完整链条：

`behaviour -> price shading -> residual mispricing -> executable positive EV`

只证明第一步：

`behaviour exists`

不允许进入候选策略。

---

### H5. Favourite-longshot bias 不是跨市场铁律

近期 Polymarket 研究对 5.88 亿笔交易做分析，发现：

- aggregate 上可以看到 longshot bias；
- 结果对 contract grouping 很敏感；
- 在其 Sports 子样本里，某些两侧 favourite-longshot pattern 反而不明显。

这说明：

> “favourite-longshot bias 已被文献证明，所以足球竞彩一定存在”

是错误推理。

对我们而言：

- FLB 是 `candidate mechanism`；
- 不是 `prior truth`；
- 需要在具体：
  - bookmaker
  - market
  - league
  - time horizon
  - grouping rule
  下重新估计。

ROOT-E 因此继续保留，但先验置信度下降。

---

### H6. Product type 和 time-to-expiry 可以单独制造系统偏差

2026 Kalshi 大规模研究显示：

- 单腿 moneyline contract 的 calibration 会随 time-to-expiry 变化；
- 临近 settlement 时价格行为发生系统变化；
- parlay 的 markup 还能独立于 leg-level calibration 出现；
- parlay overpricing 随 leg count 增长。

这进一步支持：

- ROOT-C（产品/合同）
- ROOT-D（时间/执行）

不是 ROOT-A 的附属品。

也就是说：

> 即使基础胜率概率本身已经校准，产品打包层仍可能重新制造 mispricing。

这对竞彩 M串N/过关尤其值得单独审计。

---

### H7. Joint contracts / correlated parlays 是一个独立的结构问题

2026 `ParlayMarket` 从 prediction-market 角度研究 joint contracts，核心结论之一是：

- marginal contracts 不能充分识别 joint distribution；
- parlay/joint trades 提供额外依赖结构信息；
- 如果 joint contract pricing 只是 ad hoc 乘积，会有系统性限制。

虽然其场景不是中国竞彩，但理论上确认：

> “单腿都很准”不意味着“组合合同也定价正确”。

因此 ROOT-C 中以下路线必须保留：

- correlation pricing；
- same-match dependency；
- cross-match shared latent shocks（如天气/赛程/同一球队链条等）；
- M串N payout 是否等价于合理 joint probability。

同时也要防止反向误区：

> 相关性存在 ≠ 一定有可利用错价。

只有 payout 与 joint probability 不匹配才有 edge。

---

### H8. Promotions / matched betting 属 ROOT-F，不属于核心足球研究

海外市场中：

- signup bonus；
- free bet；
- acca insurance；
- odds boost；

可以通过对冲/匹配下注变成接近机械性的收益。

这类机会属于：

`external subsidy`

而不是：

`football information edge`

对中国官方竞彩项目：

- 目前不应把海外 sportsbook promotion 当主研究方向；
- 若未来出现官方活动/返还机制，只需在 ROOT-F 中单独建事件型模块；
- 不允许把这类一次性收益混进模型 ROI。

---

### H9. v2.5 六根分类经本轮压力测试后的结论

目前新查到的理论与实证并没有出现必须新增的根级 mechanism。

所有新现象都可以归入：

- A 信息概率；
- B 市场错价；
- C 产品合同；
- D 时间执行；
- E 条件/行为价格偏差；
- F 补贴/机械异常。

所以当前可把六根分类提升为：

`EDGE TAXONOMY v0.2 — PROVISIONALLY EXHAUSTIVE AT MECHANISM LEVEL`

注意这不是说：

> 所有子策略都已经试完。

它只表示：

> 目前没有发现一种能改变投注 EV、却无法映射到 A–F 的独立机制。

---

### H10. 对旧研究“高抽水把所有常规路线杀死”的重新解释

如果旧研究最终审计后确认：

- ROOT-A 中大量公开数据/模型增量都存在；
- 但 `U_achievable < C`；
- 或多数历史正结果经修 bug 后回到明显负 EV；

那么正确结论不是：

> “足球不可研究”

而是更窄：

> **以公开信息做通用比赛概率预测，再直接对抗竞彩高 hold，这条主干可能已被结构性支配。**

这会把剩余预算自然转向：

1. ROOT-B：竞彩相对更强市场是否偶发/系统错价；
2. ROOT-C：产品/结算/组合合同是否定价不一致；
3. ROOT-D：价格更新时间和市场吸收速度是否留下窗口；
4. 少量 A×D：新公开信息出现后的短时处理优势；
5. ROOT-E：只有经过预注册和新 OOS 才允许保留的特殊子市场。

也就是说，“高抽水”不只是一个回测结果变量，而应该成为：

`Research Budget Allocator`

它决定我们还值得把多少资源花在某个根类上。

---

### H11. 未来 Edge Exhaustion Matrix 的第一层 kill 顺序

为避免再花几个月研究理论上已经不可能覆盖摩擦的路线，正式矩阵应按以下顺序杀路线：

#### Kill-1：合同可执行性

问题：
- 竞彩是否实际可买？
- 是否同合同？
- 是否有足够样本？

失败：
`KILLED_EXECUTION`

#### Kill-2：Oracle upper bound

问题：
- 即使给你完美分类/完美局部信息，理论 payout 能否覆盖 C？

失败：
`KILLED_ORACLE`

#### Kill-3：Achievable information bound

问题：
- 使用公开可获得信息，现实可达到多少？

失败：
`DOMINATED_INFORMATION`

#### Kill-4：Market-relative baseline

问题：
- 是否真的比 sharp/consensus baseline 多提供信息？

失败：
`DOMINATED_MARKET`

#### Kill-5：Multiple testing

问题：
- 这个漂亮子组是不是从大量筛选里挑出来？

失败：
`EXPLORATORY_ONLY`

#### Kill-6：Prospective replication

问题：
- 冻结规则以后还存在吗？

失败：
`KILLED_PROSPECTIVE`

只有全部通过，才有资格：

`LIVE_CANDIDATE`

这套 kill-order 比“先模型再回测”节省大量研究预算。

---

## v2.6 新增理论/实证来源

- Hegarty, T. & Whelan, K. (2025/2026). *Market structure and prices in online betting markets: theory and evidence*. Oxford Economic Papers.
- Goto, S. & Yamada, T. (2023). *What drives biased odds in sports betting markets: Bettors’ irrationality and the role of bookmakers*. International Review of Economics & Finance.
- Cain, Law & Peel (2003). *The Favourite-Longshot Bias, Bookmaker Margins and Insider Trading in a Variety of Betting Markets*.
- Dmochowski, J. P. (2026). *The profit-bias identity in sports betting: bookmaker profit as the public's prediction error*. arXiv.
- Cardozo & Rivero-Wildemauwe (2026). *The Favorite-Longshot Bias in Prediction Markets: Evidence from Polymarket*. arXiv.
- Moshrefi, N. (2026). *Prices, Probabilities, and Parlays: Systematic Bias in Sports Prediction Markets*. arXiv.
- Rana, Nadkarni, Moshrefi & Viswanath (2026). *ParlayMarket: Automated Market Making for Parlay-style Joint Contracts*. arXiv.



## v2.7 HURDLE / ORACLE / RESEARCH-STOP：把“高抽水”转成数学门槛和停止规则

> 本节目标：不再只说“竞彩抽水很高”，而是把它转成每个投注合同的**盈亏平衡门槛**，再定义不同层次的 Oracle 上界与“继续研究是否值得”的停止规则。

---

### I1. Hurdle Probability：单注的最低可盈利概率

对最简单的固定赔率、全赢/全输合同：

- 实际可执行十进制赔率：`O_exec`
- 我们对该 outcome 的真实概率估计：`p`

单注净期望：

`EV = p * O_exec - 1`

因此：

`EV > 0  <=>  p > 1 / O_exec`

定义：

`p_break_even = 1 / O_exec`

这就是**盈亏平衡概率 / Hurdle Probability**。

这比“市场平均抽水是多少”更直接，因为它完全由**你实际能买到的价格**决定。

#### 项目规则

每个候选投注必须保存：

- `odds_exec`
- `p_break_even`
- `p_model`
- `hurdle_gap = p_model - p_break_even`

只有：

`hurdle_gap > 0`

才有资格谈正 EV。

如果 `hurdle_gap <= 0`：

`PASS`

不需要再看 Kelly、仓位、组合或“信心”。

---

### I2. 如果用 proportional no-vig 作为市场参考，高抽水意味着需要固定比例的相对概率提升

设同一市场各 outcome 的：

`r_i = 1 / O_i`

book percentage：

`S = Σ r_i`

proportional no-vig：

`q_i = r_i / S`

则：

`O_i = 1 / (S q_i)`

因此正 EV 条件：

`p_i * O_i > 1`

等价于：

`p_i > S q_i`

也就是：

`p_i / q_i > S`

若：

`S = 1.15`

则模型概率必须比该 proportional market reference **相对高至少 15%** 才刚好跨过盈亏平衡。

其绝对概率差是：

`p_i - q_i > (S - 1) q_i`

例如只是数学示例：

- `q = 0.50`, `S = 1.15` → `p > 0.575`，需要 +7.5 个百分点；
- `q = 0.20`, `S = 1.15` → `p > 0.23`，需要 +3 个百分点。

这解释了为什么：

> 模型在 Log Loss / Brier 上“小幅比市场好”，完全可能仍然没有任何经济价值。

#### 重要限制

这里的 `q_i` 是：

`proportional_no_vig market reference`

不是“真实概率”。

所以这条公式用于：

- 量化市场价格门槛；
- 衡量模型需要提供多大的相对 uplift；

不能用于宣称 proportional de-vig 就是真值。

---

### I3. 一般合同不能只用 `1 / O`

对于 Asian Handicap、退款、半赢、半输等合同，状态不再只是 win/loss。

令：

- 状态 `s`
- 真实状态概率 `p_s`
- 每 1 元 stake 在状态 `s` 下的**总回款倍数** `R_s`

则：

`EV_gross = Σ p_s R_s`

盈亏平衡条件：

`Σ p_s R_s >= 1`

例如一个 quarter-line 合同可有：

- full win
- half win
- push
- half loss
- full loss

这时不能用单一：

`p > 1/O`

替代完整结算。

#### 项目规则

每个 market 必须先定义：

`Settlement Contract`

包括：

- outcome states
- gross return per state
- refund rule
- half-win / half-loss rule
- rounding
- cap（如有）

只有 settlement contract 被明确编码后才能算 EV。

这也进一步证明：

> “盘口等价”不是赔率换算问题，而是 payoff-state mapping 问题。

---

### I4. 竞彩制度层面的结构性摩擦：70% 返奖比例必须作为项目一级约束

国家体育总局体育彩票管理中心 2026 年公开材料回顾并明确：

- 2020 年 11 月 1 日起；
- 竞彩返奖奖金比例由 71% 调整为 **70%**；
- 公益金 21%；
- 发行费 9%；
- 该比例“延用至今”。

财政部、体育总局 2020 年正式通知同样规定：

- 单场竞猜游戏返奖奖金比例：70%。

**重要解释：**

这不等于：

> 每一场竞彩足球 1X2 的 overround 永远固定为 30%。

原因：

- 70% 是游戏销售额层面的资金分配/返奖制度；
- 单个比赛、单个 selection、某一时点固定奖的隐含 margin 可以不同；
- 奖金在销售过程中还会根据投注额和其他因素调整；
- 奖池/调节基金可跨场次承担差额。

因此我们必须同时保存两个不同概念：

1. `SYSTEM_PAYOUT_RATIO`
   - 制度/产品层：70%

2. `CONTRACT_HURDLE`
   - 具体比赛、玩法、selection、时点的实际可执行赔率决定。

不能把二者混成一个数字。

#### 对项目方向的直接影响

海外 sharp-book 研究常面对几个百分点的 margin。

竞彩足球的制度层 payout ratio 则说明：

> 我们研究的是一个结构性成本明显更高的执行环境。

因此任何“海外论文找到 1%–3% edge”的路线，若没有证明可以跨过**竞彩自己的 contract hurdle**，默认无经济意义。

---

### I5. 竞彩价格的时间属性是真实合同属性，不只是行情展示

中国竞彩网规则/帮助材料明确说明：

- 固定奖金会在销售过程中根据投注额和其他相关因素调整；
- 购买者完成投注时对应的固定奖金额即为最终中奖依据；
- 之后固定奖金如何变化，不影响已经完成的投注。

这意味着：

`price-at-observed-time`
和
`price-at-purchase-time`

必须区分。

#### 数据字段必须至少有

- `observed_at`
- `source_updated_at`
- `purchase_cutoff_at`
- `quoted_sp`
- `executable_sp`
- `ticket_created_at`（真钱阶段）
- `locked_sp`

只有 `locked_sp` 才是真正的执行价格。

因此 ROOT-D（Timing/Execution）不是抽象理论：

> 竞彩本身就是一个价格在销售期内变化、但购票时锁定的合同系统。

未来 shadow ledger 需要记录“当时可买价”，而不是赛后回看某个最终 SP。

---

### I6. 三种 Oracle：必须区分，否则“上界”很容易虚高

旧研究中的 Oracle 思路非常重要，但以后必须明确 Oracle 类型。

#### Oracle-0 — Clairvoyant Outcome Oracle

它提前知道最终赛果。

这不是现实可获得的信息，只能给出一个极端数学上界。

用途：

- sanity ceiling
- 检查 payoff/代码

禁止用途：

- 判断公开信息模型“还有多少可挖空间”

因为它把不可获得的未来结果当信息。

---

#### Oracle-1 — True-Probability Oracle

它不知道具体哪一场会发生什么结果，但知道赛前真实概率分布 `p*`。

在给定可执行合同集合 `J` 下：

`U_probability = max(0, max_j EV_j(p*))`

这是更有意义的**市场/价格理论上界**。

如果连 True-Probability Oracle 在某类合同上都很难跨过执行成本：

`KILLED_PRICE_STRUCTURE`

---

#### Oracle-2 — Public-Information Oracle

它只能使用在决策时点前可合法、公开获得的信息集合 `F_t`，
但假设能够以“最佳可能方式”利用这些信息。

这才是真正与我们研究资源最相关的：

`U_achievable`

现实模型只能逼近它。

如果：

`U_achievable <= 0`

或远低于实际 hurdle：

`DOMINATED_INFORMATION`

#### 项目规则

以后任何“Oracle”报告必须标：

- `CLAIRVOYANT`
- `TRUE_PROBABILITY`
- `PUBLIC_INFORMATION`

禁止只写一个 `Oracle ROI`。

---

### I7. “模型比市场好”必须拆成 Forecast Skill 与 Economic Skill

对概率预测，可以出现：

- `LogLoss_model < LogLoss_market`
- `Brier_model < Brier_market`

但：

- `EV_exec <= 0`

原因很简单：

模型虽然比市场 reference 更接近真实概率，
但改善幅度没有跨过实际可买赔率的 hurdle。

因此正式定义两层：

#### Forecast Skill

相对 reference market 的：

- Log Loss skill
- Brier skill
- Calibration improvement

#### Economic Skill

相对 `p_break_even / settlement hurdle`：

- hurdle crossing rate
- EV
- CLV
- ROI

只有：

`Forecast Skill > 0`

不能进入实盘。

必须：

`Economic Skill > 0`
并且通过 OOS / prospective。

---

### I8. Prequential Principle：为什么最终必须靠前瞻流水账，而不是继续增加历史回测

Dawid 的 prequential approach 强调：

> 对预测系统的评价，应基于它依次给出的预测与随后发生的观测，而不是依赖不可观察的参数故事。

这与我们的 prospective ledger 完全一致。

因此未来研究证据等级可正式定义：

1. `RETROSPECTIVE`
   - 历史数据回测

2. `PSEUDO-PREQUENTIAL`
   - 严格 walk-forward、point-in-time historical replay

3. `PROSPECTIVE-SEALED`
   - 当时真实生成并封存的 BUY/PASS

4. `LIVE-EXECUTED`
   - 实际锁定价格和下注记录

证据强度：

`LIVE > PROSPECTIVE > PSEUDO-PREQUENTIAL > RETROSPECTIVE`

历史数据再多，也不能完全替代前瞻 sealed evaluation。

---

### I9. Research Futility：路线研究也需要“无效停止规则”

临床试验中的 futility monitoring 有一个非常适合我们的思想：

> 当已有证据显示，即使继续增加样本，最终达到有意义效果的可能性也已经很低，应预先允许停止研究，把资源转向更有希望的假设。

我们不机械照搬临床 conditional power，
但采用相同纪律：

每个 Edge Route 在开始前写：

- target economically meaningful edge
- planned sample
- interim checkpoints
- futility rule
- reopen rule

例如：

若在预定信息量达到 50% 时：

- 观测 effect 明显远低于需要跨越的 hurdle；
- 乐观置信上界仍难跨 hurdle；
- 或 achievable upper bound 已被压到 0 以下；

则：

`STOP_FOR_FUTILITY`

而不是：

> “再换个模型、再跑半年看看”。

#### 重要限制

停止规则必须预先定义。

否则研究者看到中期结果以后再决定“什么时候停”，也会产生选择偏差。

---

### I10. Value of Information：研究本身也应该算 ROI

决策科学中的：

- EVPI：Expected Value of Perfect Information
- EVPPI：某部分参数的完美信息价值
- EVSI：收集某项新样本信息的预期价值
- ENBS：新研究价值减研究成本

可以直接转成我们的研究优先级概念。

我们不要求一开始精确算货币值，
但每条路线至少要回答：

#### EVPI-style question

> 如果这个不确定问题被“完美解决”，最多能改变多少决策/收益？

如果答案本身很小：

`LOW_RESEARCH_VALUE`

#### EVSI-style question

> 新增这批数据/这个实验，预计有多大概率改变当前 KEEP/KILL 决策？

如果很低：

`DO_NOT_COLLECT_MORE`

#### ENBS-style question

> 研究收益上限是否值得工程、数据、API、人工成本？

如果不值得：

`STOP_RESEARCH_ECONOMICALLY`

这给“什么时候停止研究”增加了一个比统计显著性更高层的理由。

---

### I11. Research Route 的四层停止机制

以后不再只有 `KILLED/SURVIVES` 一个标签。

每条路线可以在四个不同层次死亡：

#### STOP-S1 — Mechanism Stop

问题：

> 这个所谓新策略有没有改变 EV 原语？

没有：

`NOT_A_NEW_EDGE`

例：
- 再换一种 ensemble；
- 再换一个 Agent；
- 只改 Kelly。

---

#### STOP-S2 — Structural Stop

问题：

> 理论/Oracle 上界能不能跨实际 hurdle？

不能：

`KILLED_STRUCTURALLY`

这是最强停止。

---

#### STOP-S3 — Evidence Futility Stop

问题：

> 当前样本下，继续到计划样本仍有合理机会达到经济目标吗？

没有：

`STOP_FOR_FUTILITY`

---

#### STOP-S4 — Research-Value Stop

问题：

> 即使继续研究，预计减少的不确定性值不值得成本？

不值得：

`STOP_LOW_INFORMATION_VALUE`

这四层一起，才形成真正的“停止性框架”。

---

### I12. 中国竞彩执行约束应进入所有研究，不放到最后补

官方规则还明确存在：

- 竞彩总体返奖资金比例约束；
- 固定奖金销售期调整；
- 投注时价格锁定；
- 单票购买金额限制；
- 单注最高奖金限额；
- 销售时间限制。

这些都说明：

> “理论 edge”与“可执行 edge”必须从研究最前面一起建模。

因此以后任何外部策略/论文迁移到竞彩时，都要先经过：

`SPORTTERY_EXECUTION_ADAPTER`

至少回答：

- 这个 market 竞彩是否有？
- 单关还是只能过关？
- settlement 是否相同？
- 当时价格是否真的可买？
- 是否受最高奖金 cap 影响？
- 销售窗口是否允许执行？
- 组合后 rounding/cap 是否改变 EV？

答不出来：

`NOT_EXECUTABLE_YET`

---

### I13. v2.7 后的整体研究顺序

正式路线现在应改成：

`EDGE TAXONOMY`
↓
`EXECUTION CONTRACT`
↓
`HURDLE`
↓
`ORACLE / UPPER BOUND`
↓
`RESEARCH VALUE`
↓
`只有幸存路线进入 M0–M6`
↓
`PROSPECTIVE SEALED`
↓
`SMALL LIVE`

也就是：

> **先证明“值得研究”，再研究；先证明“理论能过门槛”，再建模。**

这比传统的：

`找数据 -> 建模型 -> 回测 -> 调参数 -> 看 ROI`

更适合竞彩足球这种高摩擦市场。

---

## v2.7 新增来源

- 国家体育总局体育彩票管理中心（2026）：竞彩资金分配历史与当前 70% 返奖比例。
- 财政部、体育总局（2020），财综〔2020〕42号：单场竞猜游戏返奖奖金比例调整为 70%，并规定销售时间、单票金额等约束。
- 中国竞彩网：固定奖金在销售过程中可调整，购票时对应奖金锁定。
- Dawid, A. P. (1984). *Present Position and Potential Developments: Some Personal Views Statistical Theory the Prequential Approach*. JRSS A.
- Gneiting, Balabdaoui & Raftery (2007). *Probabilistic forecasts, calibration and sharpness*. JRSS B.
- Strong, Oakley et al. / ISPOR Value of Information Task Force：EVPI / EVPPI / EVSI / ENBS 决策研究框架。
- van der Tweel & van Noord (2003). *Early stopping ... for futility: Conditional power versus sequential analysis*. Journal of Clinical Epidemiology.
- Ortega-Villa et al. (2025). *Futility Monitoring in Clinical Trials*. Statistics in Medicine.



## v2.8 SPORTTERY PRODUCT CONTRACT：把竞彩规则本身纳入可复现研究

> 本节目标：把“玩法规则”从说明文档升级成研究数据的一部分。  
> 竞彩足球的奖金、串关、无效场次、销售时间、最高奖金、返奖比例等都存在版本变化；如果历史回测使用了错误年份的规则，结果即使代码没有 bug 也不可复现。

---

### J1. 官方页面长期共存不同年代规则，必须 effective-date versioning

本轮核对官方/竞彩网公开页面时发现：

- 早期页面仍写 69%；
- 2014 年曾上调到 73%；
- 2019 年调整到 71%；
- 财政部/体育总局 2020 年通知调整到 70%；
- 国家体彩中心 2026 年公开回顾材料写明 70%“延用至今”。

这不是网站错误，而是历史规则页面长期保留。

因此研究系统禁止采用：

> “当前抓到的帮助页内容 = 所有历史时期的规则”

正式建立：

`RULESET_VERSION`

每个规则至少带：

- `rule_id`
- `effective_from`
- `effective_to`
- `source_url`
- `source_document_id`
- `published_at`
- `retrieved_at`
- `rule_hash`
- `jurisdiction/product`
- `supersedes_rule_id`

回测某一天只能使用：

`effective_from <= event_time < effective_to`

---

### J2. 竞彩固定奖金具有“动态报价 + 购票锁价”特性

官方资料明确：

- 固定奖金会在销售过程中根据投注额和其他相关因素调整；
- 购彩者完成投注时对应的固定奖金即为最终中奖依据；
- 后续价格变化不影响已购票。

因此必须区分：

1. `quote observed`
2. `quote executable`
3. `quote locked`

#### Shadow / live 数据最小字段

- event id
- market
- selection
- observed_at
- source_updated_at
- quoted_sp
- intended_order_at
- locked_sp（实盘）
- ticket id（实盘）
- ruleset version

历史回测若只有：
- 最终 SP；
- 某个日终快照；

就不能假装复现实际可成交价格。

必须标：

`EXECUTION_PRICE_UNVERIFIED`

---

### J3. M串1 的基础 payout 是固定奖金连乘：普通串关不会自动创造 edge

中国竞彩网公开示例明确：

对 `M串1`：

`奖金 = 2元 × SP_1 × SP_2 × ... × SP_M × 倍数`

若先忽略 rounding/cap，
每个 leg 的 win indicator 为 `I_i`，
joint win probability 为：

`P(all win)`

则单位 stake 的 gross expected return 与：

`P(all win) * Π O_i`

成比例。

#### 如果 legs 独立

`P(all win) = Π p_i`

因此：

`EV_gross_parlay = Π (p_i O_i)`

若每条腿：

`p_i O_i < 1`

那么：

`Π (p_i O_i) < 1`

所以普通独立串关会**复合负 EV**，不会把它救成正 EV。

这把一个旧误区彻底关闭：

> “单场都没优势，但通过串关/资金组合也许能赚钱”

在无额外产品补贴、无 joint mispricing、独立假设下，不成立。

---

### J4. 相关性是串关唯一值得研究的核心之一，但必须与 payout 错配同时出现

若 legs 不独立：

`P(all win) != Π p_i`

真实 parlay EV 取决于：

`P(all win) * quoted_parlay_multiplier`

因此相关性本身不是 edge。

需要同时满足：

> 产品 payout 使用的 joint-pricing 隐含假设与真实 joint probability 不一致，并且错配方向对购买者有利。

正式拆成：

- `DEPENDENCE_EXISTS`
- `DEPENDENCE_PRICED`
- `RESIDUAL_JOINT_MISPRICING`

只有第三个才是 ROOT-C edge。

#### 竞彩特殊注意

普通跨比赛 M串N 的赔率通常来自单腿固定奖金组合；
如果比赛之间存在共享 latent factor：

- 同赛事天气系统；
- 赛程链；
- 同球队相关赛事不可能同时出现于同一时间但可有跨日 exposure；
- 联赛级 shock；
- 规则/裁判/天气共因；

理论上 joint dependence 可能存在。

但任何“相关性策略”必须先证明：

1. dependence 可在下注前定义；
2. effect 可重复；
3. payout 没有充分吸收；
4. 跨过竞彩高 hurdle。

否则只是数据挖掘。

---

### J5. M串N 不是一个单合同，而是多个子串合同的组合

官方取消场次示例显示：

例如 `3串3` 并非一个简单“三场都中”的合同，
而可以拆成多个组合项；当某场取消时，其奖金按去除该场后的相应组合重新计算。

因此系统中不能把：

`3串3`
`4串11`
等

只存成字符串标签。

必须解析成：

`PARLAY_COMPONENT_SET`

每个 component 记录：

- included legs
- component stake
- component payout formula
- rounding point
- cancellation treatment
- cap treatment

否则无法正确计算：

- EV
- covariance
- cancellation
- payout cap
- realised return

---

### J6. 取消/无效场次规则说明“合同模拟器”必须版本化

竞彩网公开说明：

- 单场无效可退票；
- 过关中无效腿会被去除；
- 剩余组合奖金按原投注时刻的相应固定奖金计算；
- M串N 同样按组合结构处理。

这意味着：

> settlement 不只是 final score → win/loss。

必须先经过：

`event validity -> contract transformation -> settlement`

正式顺序：

1. determine match validity under ruleset
2. transform ticket components if cancelled
3. apply selection result
4. apply fixed-price lock
5. apply rounding
6. apply prize cap
7. settle

历史研究如果没有这个 contract simulator，
对少量取消/异常场次的处理可能 silently wrong。

---

### J7. 奖金上限只会降低 EV，不会创造 edge

官方规则存在不同串关场数对应的单注最高奖金限额。

设原始 payout：

`X >= 0`

奖金上限：

`C`

实际 payout：

`min(X, C)`

对任意概率分布：

`E[min(X,C)] <= E[X]`

因此 prize cap 是严格的：

`DOWNWARD FRICTION`

它不能成为正 edge 来源。

#### 项目规则

回测计算顺序：

先算 uncapped payout，
再：

`payout_capped = min(payout_uncapped, applicable_cap)`

报告必须同时显示：

- uncapped EV
- capped EV
- cap-hit frequency

如果高赔率策略大量碰 cap，
未建模 cap 的历史 ROI 必然偏高。

---

### J8. 舍入规则通常是微小离散效应，但必须精确模拟

竞彩网公开奖金计算说明采用分级计算后保留到分，并明确 0.005 的偶数舍入规则（banker-style rounding）。

单次误差上限很小，
所以它通常不是主要 edge 来源。

但对于：

- 大量组合子注；
- 高频累计；
- 临界套利检测；

必须精确实现。

#### 分类

默认：

`ROUNDING = EXECUTION FRICTION / MICRO-EFFECT`

只有在正式枚举后证明存在：
- 系统方向性；
- 可重复；
- 能覆盖交易成本；

才允许提升为 ROOT-C candidate。

不能先验假设“舍入漏洞”。

---

### J9. 最低奖金/补足规则属于潜在 subsidy，但必须核对当前 ruleset

部分历史帮助材料写过：

- 单注奖金不足某金额时由调节基金补足。

如果某项当前有效规则仍存在，
理论上属于：

`ROOT-F EXTERNAL / MECHANICAL SUBSIDY`

但因为官方页面存在历史版本混杂，
不能直接从旧帮助页推断当前竞彩足球仍适用。

因此：

- 旧规则存在 = `HISTORICAL FACT`
- 当前是否有效 = `UNKNOWN UNTIL CURRENT RULESET VERIFIED`

这类“小额补足”以后只能由 rule-version audit 确认，
不能靠页面搜索结果直接进入模型。

---

### J10. Rule Drift 本身必须进入数据 provenance

以后不只数据会 drift：

- API schema drift
- team aliases drift
- odds drift

**规则也会 drift。**

新增：

`RULE_DRIFT`

包括：

- 返奖比例变化
- 可售玩法变化
- 单关资格变化
- 销售时段变化
- 最高奖金变化
- 单票金额限制变化
- 取消场次处理变化
- rounding/cap 变化

任何跨多年回测必须同时拥有：

`DATA AS-OF`
+
`RULE AS-OF`

缺一个都不能称 point-in-time correct。

---

### J11. Sporttery Execution Adapter 的正式职责

以后外部策略进入竞彩前必须经过一层：

`SPORTTERY_EXECUTION_ADAPTER`

输入：

- generic candidate bet
- market probability
- desired contract
- decision timestamp

输出：

- whether offered
- actual market/pool
- actual line
- executable SP
- ruleset
- single/parlay availability
- max ticket
- max prize
- sales cutoff
- settlement contract
- rounding/cap treatment
- final `p_break_even`

只有 adapter 输出：

`EXECUTABLE = TRUE`

才允许进入 economic backtest。

这会阻止一种常见错误：

> 在海外 bookmaker 上有价值 ≠ 在竞彩上有可执行价值。

---

### J12. 产品层的 Kill Rules

新增以下结构性 kill：

#### `KILLED_NOT_OFFERED`
竞彩没有这个 market/selection。

#### `KILLED_NOT_SINGLE`
策略需要单关，但实际只能通过不利组合执行。

#### `KILLED_HURDLE`
实际 SP 对应 break-even hurdle 高于可实现概率上界。

#### `KILLED_CAP`
高尾部收益被最高奖金规则显著截断后失去经济优势。

#### `KILLED_RULE_MISMATCH`
历史数据与当时 ruleset 无法对齐。

#### `KILLED_EXECUTION_TIME`
信号产生时已经过停售/不可成交窗口。

这些 kill 都发生在“预测模型优劣”之前。

---

### J13. 对旧研究的一个重要审计问题

旧资产集中完成后，应专门检查：

> 历史 E10–E58 的每个 experiment 是否使用了**当时有效的竞彩 ruleset 和真实可执行价格语义**？

尤其检查：

- 是否把后来 SP 当 decision-time SP；
- 是否把只可过关市场按单关 EV 算；
- 是否忽略 cap；
- 是否错误处理无效场；
- 是否跨年份使用同一规则；
- 是否把系统返奖率与单场 overround 混淆。

如果存在这些情况：

历史结果即使没有预测代码 bug，
也必须：

`REVALIDATE_EXECUTION_LAYER`

---

## v2.8 新增官方来源

- 国家体育总局体育彩票管理中心：2026 年竞彩发展/资金分配回顾，确认 2020 年后 70% 返奖比例延用。
- 财政部、体育总局：财综〔2020〕42号，进一步调整单场竞猜游戏规则。
- 中国竞彩网：竞彩足球奖金计算、固定奖金调整、M串1奖金计算。
- 中国竞彩网：取消场次处理解释，含 M串N 示例。
- 中国竞彩网：历史游戏规则页面，用于建立 ruleset timeline，而非直接视为当前规则。



## v2.9 ROOT-SPECIFIC FALSIFICATION：每类 Edge 应该怎样被杀死

> 目标：六个 ROOT 不能都套“训练模型 → 看 ROI”模板。  
> 每一种 edge mechanism 都有自己最直接、最便宜、最有杀伤力的证伪实验。  
> 本节把 Edge Space Map 转成真正的研究程序。

---

### K1. 研究对象不再是“模型”，而是 Edge Route

定义：

`EDGE_ROUTE = mechanism × execution_contract × information_set × decision_time × segment × reference_market`

例如：

不是：

`XGBoost v3`

而是：

`A3-rest-congestion × HAD-home × public-pre-match-info × T-120min × EPL × AH-consensus-reference`

这样做可以避免：

- 换算法却重复研究同一个 mechanism；
- 不同时间点/玩法被混成一个结论；
- 一个小众子组盈利被误写成“模型有效”。

#### Route ID 最小结构

- root
- mechanism
- target contract
- reference market policy
- information cutoff
- execution cutoff
- segment
- ruleset version

模型只是 route 的一个 estimator。

---

### K2. ROOT-A 信息优势：最小证伪协议

#### 研究问题

> 新信息集合 `X` 在已有 market baseline `M` 之上，是否提供真正的赛前增量？

不允许问：

> “X 能不能预测比赛？”

必须问：

> “在知道 M 之后，X 还能不能改善 forecast / economic decision？”

#### 最低成本实验顺序

**A-TEST-1：Market-only baseline**

建立冻结 baseline：

- reference market probabilities
- same decision timestamp
- same contract

记录：

- Log Loss
- Brier
- calibration

**A-TEST-2：X-only**

用于知道 X 自身是否有信息。

但 X-only 胜过 naive 不代表价值。

**A-TEST-3：Market + X**

唯一关键比较：

`M + X` vs `M`

如果没有稳定增量：

`DOMINATED_MARKET`

无需讨论 X-only 多漂亮。

#### 必做 falsification

1. **timestamp shift placebo**
   - 把 X 人为延迟到市场已经消化之后；
   - 如果“edge”完全不变，怀疑模型其实没利用信息时点。

2. **feature permutation**
   - 在保持时间/分布大致结构的前提下打乱关键 X；
   - 若效果不降，X 的解释可能是假故事。

3. **future leak sentinel**
   - 加一个明确不能在赛前获得的 dummy/future feature；
   - pipeline 必须能在 provenance gate 主动拦截。

4. **market residual test**
   - 目标改为预测 market residual / mispricing，而不是从零预测 outcome；
   - 若只会重新拟合 market 概率，则不算新信息。

#### Kill

如果：

- proper score 没增量；
- calibration 没改善；
- hurdle crossing 没改善；

则：

`A_ROUTE_KILLED_MARKET_DOMINANCE`

---

### K3. ROOT-B 市场价格错位：最小证伪协议

#### 研究问题

> 竞彩相对一个更强 reference market 的价格差，是否在赛前可观察、可执行，并对后续结果/closing move 有预测意义？

核心不是比赛预测。

#### 必须先保证

- same event
- same market
- same selection
- same line
- same settlement rule
- timestamp aligned

否则：

`NON_COMPARABLE`

#### 最低实验

对每个 timestamp：

`gap_t = price_sporttery_t - price_reference_t`

或在概率空间：

`gap_t = p_reference_t - p_break_even_sporttery_t`

然后研究：

1. gap 分布
2. gap persistence
3. gap → later Sporttery repricing
4. gap → closing reference
5. gap → settlement return

#### Lead–lag test

若 reference move 在时间 `t` 发生，
测竞彩调整的：

- median lag
- 90% lag
- signal half-life
- remaining executable window

如果：

`lag < our observation + decision + execution latency`

则：

`KILLED_LATENCY`

即使历史上存在价差，也不可执行。

#### Falsification

- random bookmaker reference
- time-shifted reference
- next-match reference
- wrong-line placebo

真实 signal 应在正确 reference + 正确同步下明显强于 placebo。

---

### K4. ROOT-C 产品/合同错价：最小证伪协议

#### 研究问题

> 给定真实/参考的 joint state distribution，竞彩 payout contract 是否存在系统不一致？

这里的研究对象是：

`joint probability ↔ payout mapping`

不是比赛单场胜率。

#### 第一阶段：合同枚举

先完全确定：

- contract states
- payout states
- cancellation
- rounding
- cap
- M串N component decomposition

这一步不需要模型。

#### 第二阶段：No-Mispricing Null

建立一个“合同完全公平”的 synthetic simulator。

用已知 joint probabilities 生成：

- fair SP
- fair parlay multiplier
- fair M串N payout

然后把真实竞彩 payout 放进去比较。

#### 第三阶段：Dependence sensitivity

比较：

- independence
- empirically estimated dependence
- conservative dependence bounds

如果只有在一个极端 correlation 假设下才正 EV：

`BLOCKED_MODEL_SENSITIVE`

#### Kill

如果在合理 dependence bounds 下：

`max achievable EV <= 0`

则：

`C_ROUTE_KILLED_CONTRACT`

---

### K5. ROOT-D 时间/执行优势：最小证伪协议

#### 研究问题

> 某类公开信息/外部价格变化出现后，竞彩是否存在足够长的可执行滞后窗口？

时间优势本质是一条衰减曲线。

定义：

`edge(Δt)`

其中 Δt 是：

- 信息出现
- 被我们看到
- 生成决策
- 实际购票

之间的延迟。

#### 关键量

- `t_information`
- `t_reference_move`
- `t_detected`
- `t_sporttery_move`
- `t_sales_cutoff`

定义：

`usable_window = t_sporttery_move - t_detected`

再减：

- system latency
- notification latency
- human decision latency
- ticket execution latency

若剩余 <= 0：

`KILLED_EXECUTION_SPEED`

#### 必做 event study

对标准事件：

- starting XI
- key injury announcement
- venue/weather shock
- sharp-market rapid move

测：

- reference reaction
- Sporttery reaction
- decay curve
- final close

只有可重复窗口存在，ROOT-D 才活着。

---

### K6. ROOT-E 条件子市场：默认按“数据挖掘嫌疑”处理

#### 研究问题

> 一个事前定义的 segment 是否长期存在 residual mispricing？

ROOT-E 是最危险的 root，因为几乎任何历史数据都能切出漂亮 subgroup。

#### 强制流程

1. 先写 segment definition
2. 冻结 family
3. 冻结 threshold
4. 历史 exploratory
5. 新 OOS confirmatory
6. prospective sealed

#### Hierarchical shrinkage

未来若有多个联赛/球队/赔率区间，
优先使用 partial pooling / hierarchical estimate，
而不是把每个小组单独报 ROI。

目的是让小样本极端结果向总体收缩。

#### Kill

如果 subgroup 的 edge：

- 换时间窗消失；
- 相邻阈值不连续；
- OOS 不复现；
- 多重检验后不成立；

则：

`E_ROUTE_KILLED_SELECTION`

---

### K7. ROOT-F 机械/外部优势：不需要预测模型

#### 研究问题

> 是否存在由规则、补贴、错误、确定性套利造成的可重复正收益？

这类 route 的证据要求反而最简单：

- deterministic calculation
- actual executable quote
- ruleset proof
- capacity/frequency

例如：

- bonus
- rebate
- cross-market arbitrage
- payout bug

#### Kill

只要：

- 实际不可执行；
- 容量为零；
- 已修复；
- 不适用中国竞彩；

即可：

`F_ROUTE_CLOSED`

不需要收集几千场比赛。

---

### K8. Negative Controls：所有路线必须有“应该无效”的对照

未来实验模板必须包含至少一个 negative control。

例：

#### ROOT-A
- future feature 被禁止
- shuffled player info

#### ROOT-B
- unrelated bookmaker
- timestamp offset 24h
- wrong fixture

#### ROOT-C
- synthetic fair contract
- independence known-data generator

#### ROOT-D
- event 发生前的 placebo window
- unrelated news timestamp

#### ROOT-E
- pre-specified neighbouring segment
- randomized subgroup label

如果 primary signal 与 placebo 差不多：

`FAIL_FALSIFICATION`

这比只看正向结果更重要。

---

### K9. Positive Controls：系统也必须证明自己能检测“已知存在的效果”

如果 pipeline 永远得出“没有 edge”，
也可能是系统根本没有统计灵敏度。

所以需要 positive control。

例如：

- 人工植入 +5% price mispricing
- synthetic 60/40 outcome with known fair odds
- 延迟 10 分钟的 synthetic Sporttery quote
- known calibration distortion

pipeline 必须能够：

- 检测
- 定位
- 通过预期 gate

否则真实世界的 null 结果不可解释。

---

### K10. Route Evidence Ladder

每条路线不再只写一个状态。

同时记录 evidence level：

#### L0 — Mechanism-only
理论上可能。

#### L1 — Historical association
历史数据有相关性。

#### L2 — Point-in-time OOS
严格历史 as-of 可复现。

#### L3 — Prospective sealed
真实未来数据中冻结规则有效。

#### L4 — Executed
真实锁价下注支持。

#### L5 — Replicated
不同赛季/环境重复支持。

只有 L3+ 才有资格讨论“小额真钱策略稳定性”。

L1 的漂亮 ROI 不再值得兴奋。

---

### K11. 经济意义门槛必须预先定义

统计显著但经济意义极小，
在高摩擦竞彩里没有价值。

每条 route 开始前必须有：

`MINIMUM_ECONOMIC_EFFECT`

例如可以定义为：

- hurdle gap
- expected ROI
- expected value per available match
- expected value per day
- capacity-adjusted value

具体阈值由 Owner/Product Charter 决定。

目的不是追求大收益数字，
而是避免：

> 研究半年，最后证明存在 0.2% 的理论改善，但竞彩执行成本需要 10%+。

---

### K12. Capacity：正 EV 但不可规模化仍可能没有项目价值

新增：

`CAPACITY`

至少包括：

- opportunities per week
- executable matches
- maximum stake
- price persistence
- cap hit
- sales window

项目可以出现：

`EDGE_EXISTS`
但
`PROJECT_VALUE_LOW`

这两个结论必须分开。

---

### K13. Reference Market Policy 不能单一化

外部研究显示：

- overall market consensus 可以高效；
- individual bookmaker 仍未充分吸收竞争者信息；
- betting exchange 通常信息效率高，但低流动性时 bookmaker 可能给更好价格；
- speed/price discovery 随市场结构与信息事件变化。

因此 future R3 要建立：

`REFERENCE_MARKET_POLICY`

不是：

`PINNACLE = TRUTH`

候选 reference：

- sharp bookmaker
- bookmaker consensus
- exchange
- Asian handicap market
- closing consensus

每个 reference 还必须带：

- liquidity
- time
- market type
- line
- data quality

---

### K14. 最终 Route Exhaustion Matrix 的列已经可以冻结

旧资产到齐后正式矩阵建议固定以下 schema：

| Field | Meaning |
|---|---|
| `route_id` | 唯一路线 |
| `root` | A–F |
| `mechanism` | 机制 |
| `contract` | 竞彩具体合同 |
| `segment` | 事前条件 |
| `information_set` | 可用信息 |
| `decision_time` | 决策时点 |
| `reference_policy` | 市场基线 |
| `legacy_experiments` | 旧研究 |
| `external_evidence` | 外部研究 |
| `ruleset_version` | 竞彩规则 |
| `C / hurdle` | 经济门槛 |
| `A / capacity` | 可执行性 |
| `N_eff` | 有效样本 |
| `B` | baseline |
| `U_probability` | True-probability Oracle |
| `U_achievable` | Public-info upper bound |
| `negative_control` | 证伪对照 |
| `positive_control` | 灵敏度对照 |
| `evidence_level` | L0–L5 |
| `status` | KILLED/DOMINATED/SURVIVES/... |
| `kill_reason` | 停止原因 |
| `reopen_condition` | 重开条件 |

这个 schema 现在已经足够稳定。

下一步不应该继续凭空丰富列。

下一步应使用**真实旧资产**填表。

---

### K15. 当前理论框架的自然停点

到 v2.9，理论层已经完成：

1. edge mechanism taxonomy
2. execution contract
3. hurdle
4. oracle taxonomy
5. research value / futility
6. rule versioning
7. root-specific falsification
8. evidence ladder
9. capacity
10. matrix schema

再继续抽象理论的边际收益开始下降。

后续最有价值的动作是：

> 把旧研究真实实验、数据、bug、脚本逐项映射进矩阵。

这一步依赖 WorkBuddy 的 staging 交付。

所以：

`THEORY / FRAMEWORK PHASE = READY FOR LEGACY EVIDENCE INGESTION`

不是“理论最终完成”，而是已经到达：
**不读取实际资产就不值得继续空转框架** 的节点。

---

## v2.9 新增外部依据

- Elaad, Reade & Singleton (2020), *Information, prices and efficiency in an online betting market*: 整体市场可高效，但个别 bookmaker 未必充分使用竞争者赔率信息。
- Flepp, Merz & Franck (2024), *When the league table lies*: betting exchange 的信息效率及 outcome-bias 检验。
- Angelini et al. (2022), *Informational efficiency and behaviour within in-play prediction markets*: 高频 Betfair 数据下的信息反应/市场效率。
- Franck et al., bookmaker vs exchange / liquidity literature：reference quality 随 market structure/liquidity 改变。
- Frino et al. / fast trading betting-exchange literature：速度优势只有在信息窗口足够短且可执行时才有经济价值。
- 竞彩足球官方规则：固定奖金、M串N、取消场次、奖金计算和上限规则。


## Source repositories inspected

- https://github.com/martineastwood/penaltyblog
- https://github.com/probberechts/soccerdata
- https://github.com/thewongdirection/soccer-betting-strategy
- https://github.com/R1ch1k/betting-backtester
- https://github.com/sparegk/odds-quant
- https://github.com/mperi1208/value-bet-model
- https://github.com/vladapl21/odds-calibration
- https://github.com/betcode-org/flumine
- https://github.com/AnishKhetani/premier-league-data
- https://github.com/gotoConversion/goto_conversion
- https://github.com/jordantete/OddsHarvester
- https://github.com/shangfangjian1993/sporttery-api
- https://github.com/Johnserf-Seed/SportteryAPI
- https://github.com/Mrio10086/football-3x4-skill
- https://github.com/excalibur-sa/football-lottery

- https://github.com/GitSimaao/proofodds
- https://github.com/gcunharodrigues/sports-betting-ml-audit
- https://github.com/mberk/shin

GitHub popularity is not treated as scientific validity. Several high-value architectural examples are very new and lightly reviewed; every external implementation must be independently audited before reuse.


---

# v3.0 外部 AI Panel 综合裁决

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
