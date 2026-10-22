# EV-Lab TASK0036：新增跨联赛历史源与 sports-betting 原版回测验证

审计日期：2026-10-22。阶段结论：有限研究使用 ACCEPT；生产数据接入、自动投注及超额收益主张 NO-GO。

## 一、研究原则

完全复用 TASK0035 的34项文档去重结果、已经验证的18个开源项目和 TASK0034 的169场→76场独立身份桥→34场原版 Dixon–Coles 竞彩市场对照。本轮只验证仍未验证的外部数据源与原版回测器；不重复抓取原本44份ESPN文件、12份Football-Data历史CSV，不重新拟合已失败的34场模型，不安装自动下注扩展。

## 二、四个新候选的真实分类

| 资源 | 实际证据 | 结论 |
|---|---|---|
| [eatpizzanot/soccer-dataset](https://huggingface.co/datasets/eatpizzanot/soccer-dataset) | E3：六份公开数据及文档原件、SHA256、原版HF元数据、18份ESPN原始日期查询，严格新增11场三方身份联接 | 研究层 ACCEPT；上游授权与生产持续更新未获证明 |
| [withqwerty/open-football](https://github.com/withqwerty/open-football) | E2：原始目录确有亚洲、欧洲、巴西及跨平台身份库指引 | 研究地图，不是实际数据已获得的证明 |
| [schochastics/football-data](https://github.com/schochastics/football-data) | E2：原始仓库声明1,237,935历史赛果，覆盖1888—2023，ODC-BY；未用2026数据作猜测 | 旧历史备用，不能补2026当前赛季 |
| [georgedouzas/sports-betting](https://github.com/georgedouzas/sports-betting) | E3：原版0.15.1、MIT、固定HEAD eb4cedf376663fac68f508e50b83fd832e74dfd4；隔离安装成功并运行原版相关53项测试全部PASS | 有限借鉴回测接口，但只在增加严格时间门槛后使用 |

## 三、HuggingFace数据集的实际可用性

从 https://huggingface.co/api/datasets/eatpizzanot/soccer-dataset 核验仓库SHA f0cbe86bee3f28cc4b803f735a5287968741c471，lastModified 2026-07-05T01:23:18Z。原始 fixtures.parquet 12,938,933字节、SHA256 7ba90661dbed29eb940daf5ea385c7d76d5751d16be86bd9063293a982abc7b7；另外实际获取 leagues.parquet、teams.parquet、league_catalogue.parquet、data_dictionary.md、QUALITY_REPORT.md，每份 SHA256 存E盘离线manifest。

DuckDB实际统计：673,966场赛程，644,901场标记完赛。2026年10月9—20日有1,418场赛程，涉及90联赛，全部未完赛，因而此7月版本可充当真实赛前历史与赛程身份候选，却不能充当10月赛果或当前实时比赛数据。

编译者声明CC-BY-4.0，但上游包括API-Football与football-data.co.uk，编译者声明本身不能代替对上游授权和商业使用条款的核实。本阶段原件只在本地E盘证据区，不向Git公开分发。

## 四、严格三方球队身份桥：11场有增量

新选瑞超、荷甲、美职，是针对TASK0034剩余比赛的新联赛；没有重复验证原来六大联赛。ESPN swe.1、ned.1、usa.1，按官方当地/UTC日期查询，共18份原始响应全部HTTP200，逐个保存SHA256。

接受门槛：竞彩原始比赛联赛、秒级UTC开球、经过逐队人工核对的联赛限定主客缩写必须与同一ESPN事件及双方球队ID完全一致；然后要求HuggingFace对应联赛相同时刻且主、客球队全名有明确的逐队对应、匹配唯一。不能凭同一开球时点、中文名称相似或最终比分选择比赛。比分和盘口概率只在冻结ID桥之后取交集和查错。

实际新增竞彩 matchId：2041880、2041885、2041896、2041901、2041920、2041923、2042005、2042044、2042051、2042063、2042047，共11场，来自瑞超2、荷甲7、美职2。11场双方均有≥5场2025-07-01至2026-07-05前实际已完赛的球队历史；8场有已冻结严格赛前HAD以及体彩官方最终比分；进一步比分交叉复查发现ESPN与官方比分8/8完全一致，零冲突。其余原始同日多比赛/源不一致的候选明示拒绝，保留离线拒绝清单，不做模糊自动成功。

| 身份来源漏斗 | 比赛数 |
|---|---:|
| 官方原始比赛 | 169 |
| TASK0034先前独立证据通过 | 76 |
| 新增瑞超、荷甲、美职独立三方严格桥接 | +11 |
| 本轮累计可信桥接 | 87 |
| 仍无可信完整桥 | 82 |
| 最初六联赛不覆盖的89场，本轮增量后尚余 | 78 |

2025-07-01到快照发布前，三联赛实际有进球历史场次：瑞超237、荷甲309、美职570。这证明新球队历史有实质增量，**不证明11场独立模型预报能赚钱**。8场实际赛前HAD样本不足以重新调参或主张统计显著盈利。

## 五、sports-betting 原版运行与负对照

在单独的Windows E盘虚拟环境安装原版 sports-betting 0.15.1，仅基础依赖、不安装需要外部执行的扩展；对 upstream tests/evaluation/test_model_selection.py + tests/evaluation/test_base.py 实际执行 **53 passed**。

源码显示原版回测会先按DatetimeIndex排序，然后使用 sklearn TimeSeriesSplit。这一做法对乱序日期是有效的：将36个示例赛事按倒序传入，原版确实先正确排序，产生时间严格前向的三个fold，没有凭主观猜测说它会泄漏。

但将36场示例的时间均标记为同一天，原版仍能生成三个fold并计算成绩，三折均出现训练结束日=测试开始日（含同日比赛的潜在赛果提前获知风险）。不能说作者的真实实验就有前视偏差，但**原版只约束行顺序而非同日组不可拆分**。增加本仓库可复用 tools/task0036_strict_time_gate.py，强制训练集最大精确时间严格早于测试最小时间，遇同一时间或倒序泄漏拒绝；若未来接入原版回测，必须先走此门槛。不调用真实投注或自动化执行功能。

## 六、工程、证据与决议

新增 tools/task0036_hf_identity_gate.py、tools/task0036_strict_time_gate.py、tests/test_task0036_data_gate.py、research/task0036_external_source_decisions_20261022.json。本地E盘证据：E:\WebCodex-Workspace\EVLab-Data-Backups\task0036-data-source-gate-20261022，包括所有Parquet/源描述/SHA256、18份ESPN raw、TASK0036-STRICT-INCREMENTAL-BRIDGE.json、TASK0036-POST-JOIN-SCORE-QA.json、SPORTSBET_ORIGINAL_TIME_NEGATIVE_CONTROL.json。

**ACCEPT**：真实增加11场独立身份映射和前历史数据，完成原版sports-betting 53项测试并识别出需强制补足的同日时间门槛。**NO-GO**：未经上游数据权利确认不得批量生产接入；不得据此声称预测市场优势、positive EV或实现自动下注。

下一步优先核实剩余82场中真正有匹配赛事+双队ID的亚洲与欧洲杯赛数据；对无法拿到已冻结赛前历史的比赛作NO-GO，不靠增加模型数量或硬编码Kelly阈值弥补缺口。
