# EV-Lab Phase3 Independent QA — 2026-10-26

## 验收范围
研究级跨联赛大样本多模型**历史回顾性**试验，不是当时已实际采集的赛前预测、没有真实市场成交及收益。校验原始HF manifest中每个原件SHA256，再在隔离DuckDB环境用冻结配置真实跑完。

## 源、运行及输出完整性
- `fixtures.parquet` SHA256 `7ba90661dbed29eb940daf5ea385c7d76d5751d16be86bd9063293a982abc7b7`；`hf_manifest.json` SHA256 `eb3c37793866a27f8c1520c78a69e6098fdf79f08622b37fed64070fa1f8748f`。
- 实际输入54,621行，其中916完全一致的跨源重复。去重53,705，测试25,969，共181个比赛日，233类赛事。
- 模型预测覆盖：全球频率25,969、联赛频率25,969、Elo24,180、Poisson22,370；Poisson覆盖196类联赛/杯赛。
- 新源输出仅保存在独立E盘证据区；Git不上传第三方数据与逐比赛下游全量记录。
- `multimodel_summary.json` SHA256 `f867810e946d7d9d1fa942e08e6be37a020a32711c2826653a7f3daae87575e9`。
- `multimodel_details.json` SHA256 `9156dadeb36147163deef80591be069aec577668e8ca6dd7487110b0dbaa5fee`。

## QA结果
- 25,969条真实输出重查每场 `last_actual_training_date <= max_allowed_training_date`，无未来训练标签；概率归一，无非有限数字。
- 22,370场**真正同一比赛**配对：global=1.07230094、league=1.06825126、Elo=1.03262710、Poisson=1.02528810（Log Loss）；Poisson−Elo=−0.007339；按181日聚类3,000次名义CI=[−0.011536,−0.003320]。
- 六个自然月Poisson同场Log Loss都低于Elo，但差异不能宣传为全球稳定超额市场收益。
- 真实数据负对照：篡改2026-01-01源历史比赛ID329549最终比分为99:0，1月1—2日的77条预测均不变；当天及隔离日的进球不得提前进入模型。
- 六项新增单元/对抗性测试PASS；最终整仓 **387项PASS**（此前381，新增6项）。
- 完整53,705场历史、25,969条评估记录的**第二次独立全量重跑**完成；首次和重跑的两个结果文件均逐字节SHA256完全一致：summary `f867810e946d7d9d1fa942e08e6be37a020a32711c2826653a7f3daae87575e9`，details `9156dadeb36147163deef80591be069aec577668e8ca6dd7487110b0dbaa5fee`。二次输出保存于E盘新目录 `phase3-multimodel-reproduction-20261026`，未覆盖第一次。

## 核心科学限制
2026年7月封存后的HF原始赛事历史被用于重放2026年1—6月的过去场次，因此历史真实比分确证并不等于每个历史预测时刻的**信息真实发布时间**确证；这只是一项按比赛时间隔离的回顾性研究。输入不含具体竞彩价格/Pin市场，因此不能证明EV、CLV或下注资格。此阶段没有原版Dixon–Coles自动适配，也没有生产级未来球队ID映射和自动模型预测编排。

**QA Verdict: ACCEPT broad retrospective research method and observed matched baseline improvement. NO-GO production bookmaker edge or positive-EV claims.**
