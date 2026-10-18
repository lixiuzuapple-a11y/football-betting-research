# EV-Lab｜开源项目逐类验证：B 概率模型五项目（2026-10-18）

## 阶段裁决：研究审计 ACCEPT；仍未证明任何策略能超过市场
在 A 类完成后单独验证五个 B 类候选。**两个第三方原始实现真正运行，另三个达到有限源码审查 E2，绝不将 E2 写作“原版整套可用”**。没有触碰 EV-Lab 两批原始数据、原来的 135 场研究结论或云服模型；运行隔离在 Windows \`E:\WebCodex-Workspace\_evlab_categoryB_sandbox_20261018\`（非生产、非 Git），原始数据保存在 E 盘独立目录。GitHub 审计全量台账 \`research/github_category_decision_20261018.json\`。

核查六维：算法来源与依赖许可、特征输入是否市场独立、真实程序运行与归一化、数据和时间切断、反事实泄漏测试、OOS同场市场 Log Loss 与样本成本。

## 五项分级和真正完成的证据

| 候选 | 真正检查/运行证据 | 项目适配裁决 |
|---|---|---|
| [martineastwood/penaltyblog](https://github.com/martineastwood/penaltyblog) | 原始 v1.13.1 pyproject 的约20项依赖、MIT许可（LICENCE blob \`be173f45\`）；真读 \`models/dixon_coles.py\`（blob \`c35316db\`）、\`football_probability_grid.py\`（blob \`dbadefed\`），确认数值优化+低比分修正和score grid；**本轮未安装/跑原版** | **P1 保留优秀替代实现**。为避免重复重型依赖，而非默认宣称其方法强于已运行的 callumfm 版本，暂缓整包 |
| [callumfm/dixon-coles](https://github.com/callumfm/dixon-coles) | 原始 HEAD \`dea06c6e4b38085d6a4b84186cb9ead321a73ce4\`，MIT，沙箱 editable 原版0.1.0+NumPy/SciPy/Numba成功导入，**上游122项原版测试全部通过**；实际样本外同场评分+反事实复算，证据下文 | **P1 晋级独立概率模型受控研究候选**；没有足够证据证明其优于市场或值得实盘 |
| [Hicruben/theopenmodel](https://github.com/Hicruben/theopenmodel) | \`lib/model.ts\` 原版 blob SHA \`d822bd75a8d7f57e8e4a6afcadb28cad3306c911\`，重新下载后按 Git blob 算法验SHA；使用隔离 Node24 直接 import 原始TS。对Elo 1500/1500、1750/1500、1500/1750调用 \`matchProb()\`，胜平负三概率归一化且单调方向符合预期；离线实测 JSON已归档 | **P1 仅模型公式/score-grid参考**，三个smoke向量≠真实预测成绩；训练依赖ClubElo和冻结赛前输入仍未验证 |
| [yukunai/football-predictor](https://github.com/yukunai/football-predictor) | 原仓 HEAD \`b63dbcd\`，实际读 \`models/dixon_coles.py\`、\`models/backtest.py\`，有目标拟合、Elo prior、xG blend、薄样本回退、walk-forward配置；README的14个无需密钥联赛/9个API覆盖为**作者自述**。README克隆地址指向另一个GitHub owner，根目录跟踪文件未发现LICENSE | **P2 暂存借鉴架构**，先厘清实际源码权属、许可和真实数据覆盖；不直接复制源代码或宣称完整原版已测 |
| [kenRedco/football-predictor](https://github.com/kenRedco/football-predictor) | 原仓 HEAD \`60cd5ef\`，实际读 \`src/models/poisson.py\` 训练和联合进球分布（另含XGBoost/回测结构）；数据接入通常依赖 football-data.org API Key；README 152 tests / RPS数据未独立跑过，根目录跟踪文件未发现LICENSE | **P2 仅参考**，暂不引入大框架或未授权源码；需明确时间防泄漏和覆盖后才适合复现 |

## 最重要的原版OOS实测：callumfm/dixon-coles
真实上游模型**不改一行**，用我们上次实测取得的 Football-Data \`E0-2526.csv\` 英超380场有比分样本拟合，且**没有使用书商赔率也没有使用xG**；测试是E0 2026/27 60场，训练最晚日期早于测试最早日期。参数原版默认 \`lambda0=3\`, \`xi=.005\`, 设定随机种子42，未知升班马按上游自身逻辑处理。比较基准只在评分环节读取 \`AvgH/AvgD/AvgA\` 并简单去水（外部CSV赔率不代表已验证赛前真实可下注报价）。

| 指标（全部60场严格同场） | 原版Dixon–Coles | 市场去水概率 |
|---|---:|---:|
| Log Loss↓ | **1.033926** | 1.047054 |
| 3类 Brier总和↓ | **0.621327** | 0.630704 |
| Argmax准确率↑ | 43.33% | **45.00%** |

原版模型与市场Log Loss差（模型 − 市场）**−0.013128**，按比赛日成组3000次 bootstrap 的名义95%区间 **[−0.069972, +0.047811]，跨0**。因此该试验只显示**某一次60场留出模型评分略低**，不能外推为稳定能力、统计显著优势，更不能宣称竞彩正EV或盈利。

### 主动破坏未来赛果的反事实负对照
我们复制 E0-2627.csv 到隔离 \`counterfactual\` 文件夹（训练E0-2526字节完全一样），将留出赛季60场最终比分全部写成9:0，导致37场最终结果类别改变；重新调用原版Dixon–Coles完整 fit→predict。**全部60个独立预测概率和市场基准概率均与原运行逐项完全一致**，唯独基于虚构比分的损失评分改变。证明**这一次训练/预测路径没有读取测试场次最终比分**；不证明第三方代码所有路径永远无泄漏。扰动结果为QA证据，不进入任何模型成绩账本。

## 可复现与已知边界
- 原版隔离工程：\`E:\WebCodex-Workspace\_evlab_categoryB_sandbox_20261018\dixon-coles\`，HEAD如上；原版Python venv仅在同级 \`venv\`，依赖实际wheel已安装在E盘。它们不是EV-Lab生产依赖。
- 我们自己的**调用脚本**：\`tools/audit_category_b_original_dc.py\`（是驱动器，不替换上游拟合），只在运行命令时引入原版包。原始现实OOS和扰动数字文件：\`E:\WebCodex-Workspace\EVLab-Data-Backups\github_category_B_evidence_20261018\ORIGINAL_DC_60_MATCH_TRIAL.json\`、\`COUNTERFACTUAL_DC_TRIAL.json\`。
- \`theopenmodel\` 真原版源码及三个测试向量：同一个B evidence目录中的 \`theopenmodel_model.ts\`, \`THEOPENMODEL_ORIGINAL_TEST.json\`, \`verify_model.mjs\`。
- 我们独立写的回归 \`tests/test_category_b_original_dc.py\` 检查错误赔率、概率分布和 3类Brier/Log Loss计分。
- 这60场是外部欧洲英超样本，不是原169场（已验证赛果135场）。**没有球队身份表，也没有原169场当时可信的全历史特征，不能移植模型成绩到135场**。
- CSV市场报价来自下载时回溯数据，未确认报价是否为赛前或 closing snapshot。样本量小、模型参数未在独立验证集选择、开球时间/赔率PIT尚未证明，结论只作为受控方法研究。
- B类不以复杂程度决定胜负；有 MIT 与可运行并不等于必须复用，有高 Star 与自报高准确率也不等于模型已验收。

## 阶段决策与后续分类
B类 **研究审计 ACCEPT**；仅 \`callumfm/dixon-coles\` 晋级 P1 原版独立模型候选，\`penaltyblog\` 和 \`theopenmodel\` 保留分层对照，另两套不引入。**当前不接受“已证实跑赢市场”或盈利结论**。

下一阶段是 C 类4个“研究流程/QA/回测验收”项目（并非再次胡乱试模型）。逐项核验 pre-kickoff frozen snapshot、赛果重评历史不能覆盖原版、feature future perturbation、市场概率不可进入独立模型等，优先真实上游测试/原版证据、负对照；不要直接复制许可不清的代码。
