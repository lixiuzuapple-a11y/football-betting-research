# EV-Lab 开源项目 D 类：专用赛事模型与事件研究实证（2026-10-19）

## 阶段判定

D类五项已经按原仓库、许可、数据出处与可运行性逐项审查；两项在原版上做了比较深入的运行，另两项做数据/模型源码检查，另一个完成原版 Elo 单元测试。**分类/证据审计 ACCEPT，但 D类没有任何项目获准直接进入 EV-Lab 169场的独立预测或盈利判断。** 在此轮研究中，实测项目均保留原版源码，没有改写上游算法来制造通过。

研究证据分E2=原版源码/数据和许可检查；E3=直接执行原版程序/测试；出现失败需记下真实原因。源/执行沙箱：`E:\\WebCodex-Workspace\\_evlab_categoryD_sandbox_20261019`；离线取证：`E:\\WebCodex-Workspace\\EVLab-Data-Backups\\github_category_D_evidence_20261019`，只将方法、脚本及决定入库。

## 逐项验证与裁决

| 原版仓库 | 实际检查与运行证据 | 决定 |
|---|---|---|
| [ML-KULeuven/socceraction](https://github.com/ML-KULeuven/socceraction) | Git HEAD `93a1242`，MIT，原版1.5.3，声明 Python >=3.9,<3.13。使用本机 Python3.12 独立安装源码。其 Pandera0.17.2 与最新版 multimethod 2.x 冲突，沙箱锁定 multimethod1.10 才能继续。按原版测试中引用的两个 StatsBomb IDs 获取真实 `7584.json`（3715事件、SHA256 `42b2a15f...`）及 `9912.json`（3989事件、SHA256 `81294b87...`）。选定事件转SPADL与标签测试 **4 PASS**；同组完整15项测试实际为**4通过、11失败**：测试期望7584的两个旧UUID在目前公开快照均不存在，某些转换测试收到空行，不能声称上游全测通过。 | **P2保留为未来事件/SPADL/VAEP科研工具**；对当前169场赛前历史覆盖为零。 |
| [Luis-ntonio/Match_Prediction](https://github.com/Luis-ntonio/Match_Prediction) | Git HEAD `b22e501`，CC0；原版 `results.csv` 是可读取的 **49,477条真实国际赛果**，1872-11-30至2026-06-27，SHA256 `bc278465...`；原仓有训练报告、保存的XGBoost模型和特征列。原 `reports/baseline_comparison.json` 自报 calibrated Log Loss 0.8076，与本次真实独立回测无关且**未复现**。与已经审过的上游 martj42 当期49,945条/至10月6日相比，内置文件更旧。 | **P2只供国家队旧赛季方法研究**，不把国家队模型推广至俱乐部169场。 |
| [RKarnik10/world-cup-predictor](https://github.com/RKarnik10/world-cup-predictor) | Git HEAD `f6520a5`；README、requirements与脚本树实读：国家队 Elo/XGBoost、比赛权重、neutral场地、滚动趋势与Streamlit，基础结果取自 martj42 公共历史库。项目根目录Git跟踪文件**没有发现LICENSE**；没有运行作者完整训练与模型测试，README对样本外的自称无独立复现。 | **P3不进入当前EVLab模型**；国家队场景/代码许可另行核证才值得独立试验。 |
| [Divyadhole/world-cup-match-predictor](https://github.com/Divyadhole/world-cup-match-predictor) | Git HEAD `65ff37e`，MIT。原版 `tests/test_elo.py` **4项真实PASS**。但 `docs/DATA_CARD.md` 明确：随仓 `international_matches_sample.csv` **576场、2017–2024、16队，为固定种子42的Poisson生成模拟赛事**；保存 `reports/metrics-summary.json` 的Log Loss0.9841（Poisson）/0.9789（Elo）属于该合成数据，不是实际国际比赛。 | **P2仅保留软件质量/演示/赛事模拟方法**；**严禁用模拟样本成绩声称真实预测优势**。 |
| [DOsinga/football_predictions](https://github.com/DOsinga/football_predictions) | Git HEAD `8c58f54`。原版 Python `simulate.py tournaments/wc_2022.yaml --n 300 --seed 1` 和 `predict.py ... --json`均运行成功。原版 Node `test_predict.js`、`test_model_settings.js` 直接通过；`test_simulate_js.js`、`test_backtest.js` 需要从stdin传入实际YAML配置转换的JSON，补齐正确输入后都执行成功（后者 replay 1 tournament），不是之前空stdin报错后的虚假“失败”。README还明确支持在精确比分预测中**可选混入市场赔率**。根目录未跟踪LICENSE，仅 `legacy/LICENSE` 为 Apache-2.0，其涵盖范围不能默认扩张至新主代码。 | **P2保留国际杯赛模拟/赛事流程参照**；不能作为纯独立赔率模型或俱乐部研究生产组件。 |

## 对抗性验证揭示的限制

1. **上游数据版本漂移**：socceraction 测试中引用的比赛ID **7584**旧事件UUID `5171bb39-0c6c-4a3d-ae1c-756011dc219f`、`0bc3262b-7cdb-4784-b159-4409317165a7` 在最新官方7584事件数组均不存在，`9912`中的`60392108-2599-4875-bcc7-48462d530edf`存在。此为测试依赖的版本不符直接证据，不应伪称全部11项都因此失败，未逐一溯因的其余失败保留为待解决。
2. **真假样本区分**：Divyadhole 的原版模型结构能运行测试，不代表合成比赛上的成绩可迁移到现实足球，更不是竞彩正EV的证明。
3. **来源时间差异**：Luis的已保存国际历史比分截至6月27日，对比 martj42 上游10月6日更新，说明应优先检查源文件真实冻结日，而不能只看README“自动更新”。
4. **博彩赔率边界**：DOsinga 可选市场 blend 是明示模块，但一旦启用，不能再将该预测称为“完全独立于市场”。
5. **缺失跨赛事身份桥**：以上项目集中于国家队/世界杯或历史赛事事件，不能用它们的模拟或作者报告推导 EV-Lab 的169场混合比赛中胜平负优势。

## 工程入库与证据界限

- D类审计结果写入 `research/github_category_decision_20261018.json`，包括确切原仓HEAD、E2/E3级别、原版执行证据和禁止真实样本回测的限制。
- 离线资料包括 `DATA_PROVENANCE_AUDIT.json`（真实/合成的字段审查）；`DOSINGA_ORIGINAL_SIMULATION.json` 和 `DOSINGA_ORIGINAL_JS_STDIN_TESTS.json`；StatsBomb 两份实际 event JSON 在 E 盘上游沙箱中。
- Git仓库里仅登记研究证据与复用决定，**不纳入第三方无明确许可的源码、不上传大规模历史比赛和实验生成的合成结果**。
- 全仓执行 `pytest` 的结果与提交记录作为本阶段工程核验。不声称全部18个上游项目都完成全源码/全测试复现：A/B/C/D每项证据等级见正式台账。

## 18项跨类最后收束

A数据源4/4、B概率模型5/5、C研究方法4/4、D专用项目5/5，**18/18均有明确基于证据的结论**。有用资产集中在 A类的 ESPN交叉核验、B类原版 Dixon–Coles 受控概率模型、C类反事实防泄漏和冻结审计；D类更适合保持为专题资料，不扩大EV-Lab当前主线复杂度。

**研究结论依然不变：尚未证明独立模型在真实竞彩样本上超过市场；下一次主线工作应由覆盖、身份与真正前瞻样本决定，不因 GitHub 搜索发现更多算法就反复拟合同一批赛果。**
