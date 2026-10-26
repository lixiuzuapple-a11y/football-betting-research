# EV-Lab PHASE-2：云端真实新窗口 + 独立预测冻结阶段性报告

日期：2026-10-26（北京时间）。项目主线：从离线整库数据工厂推进到未来真实比赛的持续原始捕获、独立模型概率冻结。

## 总体判定

- **Cloud STARTUP ACCEPT**：从固定已审计官方采集代码，在全新root启动48小时上限、2分钟独立健康监测；真实首批及连续10笔成功、原始源哈希和SQLite完整性验证通过。
- **PROSPECTIVE FORECAST FREEZE ACCEPT（弱基线）**：4场10月27日未来真实竞彩比赛，在开球前一次冻结4个独立1X2概率向量、2个合格HAD市场参考向量和所有原始输入哈希。
- **LONG-RUN PENDING**：48小时采集完整性不可能在启动当天验收，且本轮未测试掉电重启恢复。
- **MODEL ADVANTAGE/CLV/PROFIT NO-GO**：仅常数类别频率弱对照，无样本外新赛果表现。不是生产级多模型竞争系统、也不存在已证实BUY。

## A. 云端已完成的实测

原源码 `tools/task0017_official_only.py` 的冻结Git版本 `eb1099a799d86d16d9ca625501641a264d1c2f91` 与云端 `/home/ubuntu/task0024_collector.py` 的SHA256逐字节一致：
`a3ae6db246ba2cd52cdfc3798efe66462fc27d13fb11a8d5345572c4144b162a`。

真实服务 `evlab-phase2-official-20261026.service` 约14:08 CST 启动，独立新数据根
`/home/ubuntu/evlab-data/phase2-official-20261026`。
- `User=ubuntu`、`MemoryMax=350M`、`RuntimeMaxSec=49h`、`Restart=no`；采样60秒、超时20秒、最多2880轮和连续3次失败终止。
- `evlab-phase2-health-20261026.timer` 每2分钟运行（先手工检查一次），记录最新采集延迟/SQLite quick_check/磁盘空间到 `health.jsonl`。
- `evlab-phase2-health-stop-20261026.timer` 50小时后停止此监控timer，避免永久遗留。
- 06:08:42 UTC首次HTTP200，4场，原始sha256 `59a70aff5050426b94d69270907f2b9253268f6b9c54ec04e7a0dfac538380ae`，写入新SQLite，quick_check=ok。
- 06:18:41 UTC只读复核：10笔捕获；最近每2分钟巡检均 `status=OK`（其中06:12、06:14、06:16、06:18），服务 `active/running`，捕获最新状态 `ok`，没有覆盖任何历史目录。

注意：systemd-run临时单元**不会保证机器重启后自动恢复**；本阶段是有边界工程资格测试，不是已验收的永久生产环境。轮次未满、未来故障未知，决不能写“连续48小时成功”。

## B. 独立概率与市场基准相互隔离

`src/football_betting/models/observed_frequency.py` 实现真实独立基线：
- 只读有SHA256来源的135条官方历史完赛比分（日期截至2026-10-18），训练类别分布主胜64/平局31/客胜40。
- Dirichlet(1)三分类平滑，固定版本 `observed-frequency-dirichlet-1-v1`，概率固定为 `[0.4710144928,0.2318840580,0.2971014493]`。这仅证明流程和极弱无信息基线，可用于检测市场是否具备优势，不能代表成熟模型。
- 4条预测的冻结时间为2026-10-26 06:16:58 UTC（北京时间14:16:58），均早于10月27日开赛。逐条匹配正式 `Match` / `PredictionRequest` / `Prediction` 接口，带版本、训练源与预测ID。
- 从真实官方raw + 独立manifest经TASK0040源哈希与严格HAD准入，4场独立预测中仅2场附带有效的竞彩HAD对照；另外2场非零HAD状态位，市场对照拒绝。
- 数据截止、训练状态与市场参考信息各自留证；任何未来赛果都没有进入此冻结文件。

**首份独立未来预测冻结文件**仅在E盘归档（Git不分发原始第三方字节）：
`E:\WebCodex-Workspace\EVLab-Data-Backups\phase2-forward-lab-20261026\PHASE2-FIRST-FORWARD-FREEZE.json`

预先提交至Git的完整文件SHA256：
`53abdeb13121974512ead40340fbd68df96a5082ab8fde210b84bf3588b40f86`。

训练标签SHA256：
`6da5c08d4b1a77f531506c67052fdd46cc002e8562283b02ca7d85a1b64c1a40`。

官方原始报价SHA256：
`4079741dcbd9f9dd7ef65bd241da9f0592988b2bdb33e62aee0cb04857331457`。

**重要限制：** 新预测创建于14:16，而本次引用的市场参考报价收到时间是11:49。两者不是严格同时点成交价；本阶段不对盈利或CLV作任何推断。

## C. 测试与独立QA

新增7项测试：真实预测有概率和市场隔离、赔率扰动不影响独立预测、市场被拒绝仍能保留独立预测、拒绝赛后冻结和未来训练标签、结果期前拒绝评分与球队身份冲突拦截、没有赛果则不凭空评分、不可覆盖已有冻结文件。

`python -m pytest -q tests/test_phase2_forecast_lab.py` 7项PASS；截至本轮 `python -m pytest -q` 整仓 **381项PASS**。

独立只读文件复核：冻结文件SHA256与预提交一致，4/4预测时间早于开赛、概率归一，训练数量135和三个类别64/31/40吻合，2/4市场对照严格通过，无BUY/赛果字段；云端见上文只读SQLite/systemd/health检查。

## D. 下一阶段的能力边界

已交付“云端有界连续获取”和“独立概率与市场对照分层冻结”的**可用最小纵向链路**。

尚未完成：
- 云端48小时连续运行闭环与重启告警恢复验收；
- 自动将云端新抓的数据送至统一数据工厂和预测冻结任务；
- 原版DC/Elo按可获得可靠历史特征的比赛群体自动训练/滚动回测的统一多模型竞赛；
- 完赛后合法可靠的自动结果获取与未来真实评分；
- Pinnacle同时点基准、可执行报价、真实CLV、正EV证明及投注行为。

后续应按完整工程能力推进，不在几场比赛上反复调参刷结果。不得把弱基线升级为成熟模型的宣传。
