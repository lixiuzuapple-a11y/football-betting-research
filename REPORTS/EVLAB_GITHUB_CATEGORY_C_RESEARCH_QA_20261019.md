# EV-Lab GitHub C类：研究方法与验证框架逐项验收（2026-10-19）

## 验收口径

分类账本 `research/github_category_decision_20261018.json` 中C类4/4已逐项实证审查。原版项目源码保存在独立Windows沙箱 `E:\\WebCodex-Workspace\\_evlab_categoryC_sandbox_20261018`，不复制上游源代码进入EV-Lab。验证分层：E2为原版源码检查；E3为确实调用原版代码/测试。A、B类结论不因此重新打开。本报告验证研究纪律，而不是宣称模型预测更优。

| 项目 | 具体证据 | 验收决定 |
|---|---|---|
| [dank0i/football-forecast](https://github.com/dank0i/football-forecast) | Git HEAD `32417ea`；真实运行上游 `tests/test_leakage.py` 中两个指定反泄漏用例，2 passed / 8 deselected。改写未来20场结果不改变过去Elo；本场得分不污染赛前form。仓库根目录未找到LICENSE | **接受反事实测试思想，不复制无许可源码**；其16k+场作者成绩未经独立复现 |
| [alexander-quang-phan/football-match-outcome-prediction](https://github.com/alexander-quang-phan/football-match-outcome-prediction) | Git HEAD `e7b967e`；MIT许可；`prepare_match_training_data.py` 的 `shift(1)` 5/10场滚动特征、pre-match Elo；`train_match_prediction_models.py` 明确训练<=2022、验证<=2024、2025留出。README所述比赛后排名泄漏作为风险案例 | **仅接受源码级时间纪律参考**；未复现作者2025模型成绩 |
| [OPaheimer/premier-league-predictor](https://github.com/OPaheimer/premier-league-predictor) | Git HEAD `79dc7a3`；上游 `test_weekly_loop.py` 原版10 passed（隔离env补充PyYAML）；再次直接调用其原版 `_upsert_ledger`，同一matchweek重评分使账本accuracy从0.55覆写为0.99，仍仅一行，`UPSTREAM_LEDGER_REWRITE_TEST.json` 有离线原件 | **部分接受 freeze/grade/merge-fail guard；明确拒绝可覆写ledger作为EVLab sealed证据**；此为上游设计功能不必称bug |
| [kaspersgit/football-prediction-autoresearch](https://github.com/kaspersgit/football-prediction-autoresearch) | 原版 `src/model/features.py` 明示 `market_h`、`market_d`、`market_a`、`market_overround` 等赔率特征；源码级E2，原版训练程序未运行 | **禁止接入EV-Lab独立预测层**；只把实验登记/冻结纪律当研究参考 |

## 本地真实验收 / 反例
- 运行上游 `football-forecast` 指定2项防泄漏测试：**2/2 PASS**（不能概括为该项目全部测试）。
- 运行上游 `premier-league-predictor` 对应10项 `weekly_loop` 测试：**10/10 PASS**；以原版函数实际证实可覆写同一比赛周评分。
- EV-Lab自主编写 `tests/test_discovery_temporal_adversarial.py` 在原两项反事实检查上新增第三项：**同一日比分修改不改变当日赛前预测，但允许改变随后日期预测**。针对EVLab `task0032` 模块实测 **3/3 PASS**，不直接复制上游测试代码。
- 反例证据路径：`E:\\WebCodex-Workspace\\EVLab-Data-Backups\\github_category_C_evidence_20261018\\UPSTREAM_LEDGER_REWRITE_TEST.json`。本地沙箱及测试数据不上传到普通Git。

## 不盲从与边界
- 过去样本外预测、市场赔率是否独立，是单独的研究门槛；有防泄漏测试不能替代真正的前瞻sealed评估。
- `_upsert_ledger` 可覆盖历史评分不一定意味着预测本身作假，但**不符合本项目冻结研究证据的不可覆写要求**；需使用新版本和修订链。
- 未证实作者的收益、准确率或全部模型代码；没有把赔率特征偷偷加入独立预测器。
- C类已验收，D类5个专用项目依然PENDING。完整18条分类归属保持唯一且无遗漏。

**阶段决议：C类研究方法审计 ACCEPT；采纳测试思想和流程约束，拒绝任何破坏EVLab证据冻结纪律的代码直接复用。**
