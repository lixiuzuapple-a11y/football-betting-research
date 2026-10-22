# EV-Lab TASK-0035 — 外部《足球彩票量化预测系统》文档去重、证据纠错与有限新增实测

**审计日期：2026-10-22｜阶段：ACCEPT（文献去重与评分诊断），NO-GO（按文档重建整套系统或宣称已有正EV）**

## 一、范围、规范与去重结论

- 原文： [足球彩票量化预测系统：全网深度调研与Agent开发执行规范](https://docs.google.com/document/d/1fE54qOUPNA1WaWtbz470lsIDZv01v4zHQTYwj2eQJms/edit)（Google Docs documentId `1fE54qOUPNA1WaWtbz470lsIDZv01v4zHQTYwj2eQJms`，读取时180个段落）。
- 已按原文**10条论文、9个GitHub仓库、10类数据源、5个开发阶段**形成34条逐项去重决策。机器可读表：`research/task0035_document_dedup_ledger_20261022.json`。**A：9条已审，直接复用；B：14条有明确缺口，仅补增量；C：7条真正新增的研究/工具候选；D：4条现阶段拒绝或无关**。新增外部发现3个另列，绝不混成原文条目。
- 对照依据：此前 `research/github_category_decision_20261018.json` 的18项目E1/E2/E3分级，`REPORTS/EVLAB_GITHUB_CATEGORY_A_DATA_AUDIT_20261018.md` 至D类报告，以及`REPORTS/EVLAB-TASK0034-REAL-IDENTITY-AND-DC-20261019.md` 中169场→76场身份桥→34场独立DC同场市场研究。**绝不再跑旧18项目全套测试或为写报告重新抓取44份ESPN原始数据**。
- 文档声称经交叉验证、并附带Coding Agent规范；这属于第三方资料**待核验主张**，不能将它的Prompt当我们执行命令。真实适配仍由现有GitHub canonical state决定。

## 二、发现的需立刻纠正的证据风险

**1. 2025年作者正式勘误推翻原文利润数字（高优先级纠错）**

- 文档仍引用 Walsh & Joshi (2024) 按校准选模平均ROI **+34.69%**，对比按准确率选模 **−35.17%**；该研究其实实验领域为**NBA篮球**，不是中国竞彩足球。
- 作者在2025年正式勘误指出特征工程实现有错误，影响原结果；**校准选模更正后平均ROI −9.77%，准确率选模更正后平均ROI −26.78%**。最佳设置可以为正，但**平均为负**。方法对比结论方向仍在，并不支持原文所谓常态+34.69%盈利。
- 证据：[University of Bath Corrigendum](https://researchportal.bath.ac.uk/en/publications/corrigendum-to-machine-learning-for-sports-betting-should-model-s/)、[Corrigendum DOI](https://doi.org/10.1016/j.mlwa.2025.100627)、[作者更正代码仓库](https://github.com/conorwalsh99/ml-for-sports-betting)（该仓库已归档，README明确写已修正错误；MIT许可证真实核验）。**不重复复现原版含错误的盈利试验**。

**2. 2019年 Hubáček 等的去相关/组合优化盈利证据主要来自NBA，并非足球市场**

- 官方 [International Journal of Forecasting 2019 原论文](https://doi.org/10.1016/j.ijforecast.2019.01.001) 说明其正盈利历史实验使用美国NBA 2007–2014年数据。概念有借鉴意义，但不能凭文章直接把市场去相关、组合优化搬成竞彩足球已验证Alpha；本阶段不写下注组合引擎。

**3. RPS不是唯一合法评分，Log Loss与Brier亦有研究价值**

- Constantinou & Fenton 2012确实倡议 **RPS** 处理其视为有序的胜/平/负；但这不构成其它严格适当评分规则均失效、或者模型只能按RPS选型的证明。[2012论文元数据](https://ideas.repec.org/a/bpj/jqsprt/v8y2012i1n12.html)。
- EV-Lab 保留预先已报告的三分类 **Log Loss / Brier**，新增 **RPS** 用于相同冻结概率的诊断，**不更改34场选择、不重训、不调整模型或从RPS挑选模型**。这种做法与数据源取证及模型/市场隔离原则一致。

**4. 去水公式与“收盘线真值”必须区别理论与可用证据**

- 文档要求必须用Shin/Power并声称还原真实概率。实际 Shin、Power、Multiplicative 是不同假设下的**市场隐含概率估计器**，没有单一公式能保证恢复真实概率。Erik Štrumbelj 2014对 Shin 给出支持；[Clarke等2017](https://www.sciencepg.com/article/10.11648/10026106) 发现 Power 很有竞争力。应在**同一时间戳冻结赔率**上事先确定比较方案，而非看见结果后选有利公式。
- TASK0031/TASK0034已用 `1/odds` 归一化消除常规Overround；不是对原赔率直接1/odds作为概率，当前可保留为基准。Shin/Power **仅作为待确认校准的敏感性试验**，绝不先假定它们在国内竞彩肯定更准确。
- Pinnacle去水收盘概率不是每场比赛的可观测客观“真值”；CLV是赔率执行和收盘前真实报价的**代理诊断**，不能凭50–100次样本或t检验自动宣布Alpha。缺真实下注/收盘时点就必须写缺失，不能生成虚构CLV。参见 [Pinnacle / Buchdahl 对CLV的讨论](https://www.pinnacle.bet/betting-resources/en/betting-strategy/using-the-closing-line-to-test-your-skill-in-betting/7e6jwjm5ykejuwkq)。

**5. 模型架构与“高抽水固定阈值”都不可直接照搬**

- Doc Phase1完整五大联赛数据采集、ESPN/Football-Data身份归一化已具备真实样本；重造 `src/data_pipeline/` 没有增益。
- Doc Phase3要求必装penaltyblog+CatBoost、Pi-ratings并按RPS调组合权重。但原版callumfm Dixon–Coles已在34场中国竞彩同场独立评估，Log Loss **1.028665 vs 市场0.933863**，并无优势；新增更复杂算法、使用同一批34场寻优会扩大过拟合风险。
- Doc Phase4默认 EV>4%，国内竞彩6–8%和¼ Kelly / 每场3%本金的参数缺少本地校准及真正可执行赔率数据证明；在没有可复现正EV前，不作为生产默认或自动下注策略。

## 三、只有评分指标新增的最小真实复算：34场原版输出保持不动

新增 `tools/task0035_rps_score_audit.py`，只读取 E盘 `TASK0034-SPORTTERY-ORIGINAL-DC-SCORING.json` 和原来60分钟前置截止 `TASK0034-60MIN-CUTOFF.json`。采用三分类 H-D-A 顺序、两条累积概率阈值均方误差，除以 K−1=2。原版模型及市场去水概率**不做任何改动**，用相同比赛真实结果评价。

| RPS（↓） | 原版独立Dixon–Coles | 同场竞彩去水市场 | 模型减市场 |
|---|---:|---:|---:|
| 冻结34场（8日期） | 0.195172 | **0.166459** | +0.028713 |
| 赛前≥60分钟33场（8日期） | 0.196914 | **0.167631** | +0.029284 |

34场日聚类5000次重抽样 RPS差的名义95%区间 **[+0.006957,+0.039947]**，33场 **[+0.006934,+0.041116]**。仅8个比赛日期簇，名义区间不可过度解释；**新评分没有推翻既有结论**，没有主张投注盈利、交易回报或样本外泛化。

## 四、真正新增GitHub项目：只做一手源码/许可审查，不假装E3完整验收

| 工具 | 现阶段原版证据 | 增量判断 |
|---|---|---|
| [georgedouzas/sports-betting](https://github.com/georgedouzas/sports-betting) | 原版pyproject MIT、Python>=3.11,<3.14；真正读取 `src/sportsbet/evaluation/_base.py` blob `24a4f479...` 中数据X/Y/O分离、赔率列快照语法与Backtest接口；可选MCP及playwright真实投注执行 | **P1：隔离、无钱、无执行模式**下进一步核验时间泄漏/赔率字段与现有EV-Lab测试框架；严禁默认安装下注执行层或信任其演示ROI |
| [PySport/kloppy](https://github.com/PySport/kloppy) | 原版pyproject v3.19.1、BSD-3 LICENSE和轻量标准化依赖已核查 | **P2：仅当已有合法实时赛事事件/追踪数据时再做PoC**，不能解决当前169场的球员事件来源覆盖 |
| [kochlisGit/ProphitBet-Soccer-Bets-Predictor](https://github.com/kochlisGit/ProphitBet-Soccer-Bets-Predictor) | 原版README/更新记录核查；GitHub root LICENSE路径未发现，重型GUI及安装建议；作者盈利判断未复现 | **P2/NO-GO整体安装**，只记录可能的辅助方法；不更改Windows Python安装以迎合其向导 |
| [conorwalsh99/ml-for-sports-betting](https://github.com/conorwalsh99/ml-for-sports-betting) | 原作者修订后完整源码GitHub仓库，归档状态；LICENSE MIT，README明确修正了影响原ROI的错误 | **重要的是论文更正，不是复现NBA投资收益** |
| [JaseZiv/worldfootballR](https://github.com/JaseZiv/worldfootballR)、[ewenme/understatr](https://github.com/ewenme/understatr) | 前者仓库已归档；后者R DESCRIPTION版本1.0.1.9000，MIT许可 | Python soccerdata已研究过，**低优先级、避免跨语言重复造源** |

本阶段没有安装这些新工具的完整运行时，没有把E2源码阅读说成E3工作验证。对上游 README 中 ROI、许可、数据覆盖等自述分别标识证据等级。

## 五、审计过程中另发现、但不混入原文34条的3个数据候选

- [withqwerty/open-football](https://github.com/withqwerty/open-football)：开源数据索引，提示欧洲、世界、亚洲与美洲非五大联赛源及球队身份层。**只证明存在索引，不证明2026每场都有可用分数**。
- [v-eatpizzanot/soccer-dataset](https://github.com/v-eatpizzanot/soccer-dataset)：README公布271联赛和大量比赛/赔率等数据，是**优先下一轮E3覆盖实测候选**；但实测前不能把README数量当作可用于剩余89场的真实覆盖，更须核实API-Football来源授权、比赛开始前可得时间、赛事ID及空值处理。
- [schochastics/football-data](https://github.com/schochastics/football-data)：广泛且较早期历史比分的参考，有望充实时间序列训练，但最新年份需实地确认，**不能自动填充2026即时状态**。

## 六、后续决策

**本阶段完成**：所有34条文档主张被映射至既有证据/待核验缺口；2025勘误与跨运动错误已纠正；第三方新代码实看过源码和许可；用冻结34/33场实做RPS，结论不变；A类旧功能和18仓库测试没有重复跑。数据仓库所有原始竞彩及外部数据保持只读。

**下一条主线优先级**：与其再建一个Agent五阶段框架，优先对新数据源（尤其亚洲、欧洲二级赛事）做真实比赛ID/合法赛前历史覆盖门槛测试；如果E3没有通过，不把复杂CatBoost、Pi或凯利等强行嫁接到现有34场。sports-betting仅在验证出我们欠缺的QA/backtest能力时才有限纳入。

**明确不做**：复用已被2025年正式勘误否定的+34.69% ROI、硬编码未经验证的正EV门槛、模拟实际下注及自动投注。

证据分级、逐条采用/拒绝或待实测清单详见机器账本。
