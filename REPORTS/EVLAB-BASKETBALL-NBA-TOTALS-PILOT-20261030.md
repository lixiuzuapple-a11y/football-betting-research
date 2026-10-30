# EV-Lab 篮球支线｜NBA 赛季初大小分小型实证（2026-10-30）

**阶段判断：已执行 / 研究结论 NO-GO（本固定假设）；数据源 REJECTED for formal betting/EV backtest。**

这是 Owner 2026-10-30 授权的一次**有界探索例外**，不代表此前“足球结项后才正式启动篮球”的备忘失效。没有启动新篮球服务、持续采集、交易、收费订阅，也没有改动足球现有任务和部署。

## 1. 样本、冻结规则与来源

- 预注册文件：[`research/experiments/NBA-TOTALS-EARLY-SEASON-PILOT-PREGISTER-20261030.md`](../research/experiments/NBA-TOTALS-EARLY-SEASON-PILOT-PREGISTER-20261030.md)，在运行结果前落盘。
- 数据源公开仓库：<https://github.com/aaryanshah607/nba-line-sheet>；实际下载：<https://raw.githubusercontent.com/aaryanshah607/nba-line-sheet/main/nba_odds_clean.csv>。自述的汇总源仍未逐项核证；不视为经过审计的 Pinnacle/竞彩盘口。
- HTTP 200；原始文件 **3,683,246 bytes**；SHA256 **`fe37302d1f6c6b12b619e1b4a507ad7c23df467d988f83df7a3e7e268ce6ee52`**。本地只保留于 Git 忽略的 raw 路径 `data/raw/nba_totals_pilot_20261030/`，不将批量原始数据入仓库。
- CSV 输入 **23,609 行**；期内对照只使用日期、对阵、总分线 OU、最终总得分。赛季开始后 0–29 天 = early；30–119 天 = comparison；赛季 2007–2020 供探索，2021–2025 是冻结留出期。严格不根据赛果重新挑选分组边界。
- 公开仓库 README 称 **23,586 场**，与所取 CSV 的 23,609 行不一致；需上游解释，不能自动断定两者为何不同。

## 2. 第一遍：照原冻结规则计算（但数据质量未通过）

| 指标 | 2007–2020 探索 | 2021–2025 留出 |
|---|---:|---:|
| early 有效判定场次 | 2,886 | 1,106 |
| early 大分比例 | 47.2626% | 50.1808% |
| comparison 大分比例 | 50.6816% | 50.4979% |
| early − comparison | −3.4190 pp | **−0.3171 pp** |
| 双侧近似 p 值 | 0.00159677 | **0.85818323** |

留出期根本无法复现探索期的偏差（只有 2/5 个留出赛季同方向），已不满足固定统计门槛，**不得宣称存在稳定的开季小分优势**。这是按冻结分组计算出的数字，但因源数据错误不能作为正式质量过关的确认性研究。

## 3. 数据质量问题（直接阻断正式结论）

1. CSV 发现 **23 行明显不合理记录**，例如 OU=1、3、1955.5、1111、比赛总分=0 或 22。首次冻结计算保留了它们；敏感性审计另行剔除，不隐瞒原始结果。
2. NBA 2019–20 停赛复赛/季后赛跨至 2020 年秋天，按普通月份映射会把 2020-09 的季后赛当成下一赛季开始；因此原冻结运行中“2020 赛季首日=2020-09-01”，**这一赛季分组不合格**。
3. 2025–26 记录只延伸至 **2026-01-07**，而本次调查日在 2026-10-30；它是未覆盖该完整赛季的过时文件，留出期的最后一年不完整。
4. 无独立比分核对、盘口来源、赔率/报价时间戳、对应市场两侧价格；不能判断是否为开盘/收盘，更不能模拟中国竞彩实际可投注赔率、CLV、EV 或 ROI。

## 4. 第二遍：事后质量敏感性检查（不是重新预注册）

**目的仅为说明原始失败是否很容易被异常行扭转，不是改出一个更好看的胜率。** 剔除 23 条不合理数值；整季剔除异常赛季 2020 与截断赛季 2025；未调整 30/120 天阈值、研究目标或统计方法。

| 指标 | 2007–2019（剔除 2020） | 2021–2024（剔除 2025） |
|---|---:|---:|
| early 有效判定场次 | 2,849 | 882 |
| early 大分比例 | 47.3850% | 48.8662% |
| comparison 大分比例 | 50.6995% | 51.4147% |
| early − comparison | −3.3145 pp | **−2.5485 pp** |
| 双侧近似 p 值 | 0.00234838 | **0.19365981** |

敏感性样本的留出期同样未达到统计门槛。该数据来源不足以支持任何真实下注边际收益推断；同时不能据此断言 NBA 大小分市场在其他数据集或更具体的条件下绝无可利用偏差。

## 5. 可重复性和 QA

在 EV-Lab 项目根目录：

```powershell
python tools/nba_totals_early_pilot.py --input data/raw/nba_totals_pilot_20261030/nba_odds_clean.csv --output research/experiments/NBA-TOTALS-EARLY-SEASON-PILOT-RESULT-20261030.json
python tools/nba_totals_early_pilot.py --sensitivity --input data/raw/nba_totals_pilot_20261030/nba_odds_clean.csv --output research/experiments/NBA-TOTALS-EARLY-SEASON-PILOT-SENSITIVITY-20261030.json
python -m pytest tests/test_nba_totals_early_pilot.py -q
```

- 固定结果：[`NBA-TOTALS-EARLY-SEASON-PILOT-RESULT-20261030.json`](../research/experiments/NBA-TOTALS-EARLY-SEASON-PILOT-RESULT-20261030.json)
- 事后质量敏感性：[`NBA-TOTALS-EARLY-SEASON-PILOT-SENSITIVITY-20261030.json`](../research/experiments/NBA-TOTALS-EARLY-SEASON-PILOT-SENSITIVITY-20261030.json)
- 合成样例单元测试 **4 passed**，覆盖 PUSH 结算、概率区间、季节归属、重复键与异常值处理。EV-Lab 全仓测试 **434 passed in 14.47s**。单独 Ruff 检查因本地没有安装 `ruff` 未能执行，不将其记为通过。

## 6. Owner 可决策的结论

- **NO-GO**：不给“仅凭 NBA 开季前 30 天就长期倾向小分”的简单策略配置任何开发或实盘预算；第一轮冻结测试未复现。
- **REJECT 作为正式下注回测数据**：当前第三方 CSV 的质量、赔率时间证据、赛季完整性不足，不可继续据此做宣称盈利的篮球系统。
- **继续值得研究的方向**（足球结项后再考虑正式启动）：(a) 先核查带时间戳的实际盘口与对应赔率；(b) 伤病/阵容信息披露到盘口反应的时差；(c) 真实可用价格下的概率校准。不能因为本次负结果就否定全部篮球研究。

**状态：研究 SPIKE 已收束；不升级为长期篮球 TASK，不触碰足球主线运行中服务。**
