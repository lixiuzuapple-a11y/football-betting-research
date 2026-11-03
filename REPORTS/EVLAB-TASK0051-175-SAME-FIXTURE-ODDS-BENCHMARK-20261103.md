# EV-Lab TASK0051：175场同场国际赔率对照

**日期：**2026-11-03。**裁决：**回顾性探索性市场对照ACCEPT；真实PIT定价优势与正EV为NO-GO。

## 1. 来源与时间

**EV-Lab模型：**2026-10-26 Phase3已经冻结的25,969场历史逐场预测，2026年1月至6月滚动评价；本次没有改变任何模型参数、训练样本或预测值。

- Phase3逐场预测`multimodel_details.json` SHA256：`9156dadeb36147163deef80591be069aec577668e8ca6dd7487110b0dbaa5fee`。
- TASK0036历史赛事实体`fixtures.parquet` SHA256：`7ba90661dbed29eb940daf5ea385c7d76d5751d16be86bd9063293a982abc7b7`。
- 市场来源：<https://tipsaudit.com/data>；该站明确提供CC BY 4.0许可，CSV为<https://tipsaudit.com/data/tipsaudit-predictions.csv>，2026-11-03只下载一次。2026-11-01站点公开快照共7,794条赛事预测记录；源CSV SHA256：`cfdec6a9559137f52e39822855fc963f55c4a9810736f258ec258752ae9f0883`。
- 来源署名：TipsAudit (2026), TipsAudit Football Prediction Dataset: fair odds, closing line value and bookmaker margins, https://tipsaudit.com/data — CC BY 4.0。

曾核验Football-Data一个欧洲联赛CSV的字段结构，但该站限制自动/AI及非个人数据用途，**没有将其数据纳入本次评分，也没有进行批量抓取**。

关键时间缺口：TipsAudit的`pin_open_*`是其首份记录价格，**不是**Pinnacle独立认证的开盘，更不证明在EV-Lab历史预测时已可获得；部分报价可能在站点预测记录之后才出现，网站承认有些记录是赛后回填。此CSV在比赛结束数月后获取，`record_hash`也不是独立可信的PIT时间戳。

## 2. 样本身份审计

交集由数据可获得性确定：市场样本自2026-06-11开始，Phase3测试到2026-06-30，故窗口固定为2026-06-11～2026-06-30。

| 条件 | 场数 |
|---|---:|
| 交集窗口中的市场候选 | 237 |
| 严格同场身份、比分一致且三项市场价完整 | **175** |
| 不能唯一核验的赛事身份/时间 | 62 |
| 不同历史赛事ID类型 | 11 |
| 有合格样本的UTC日期 | 19 |
| 历史比分/第三方结果冲突 | 0 |

匹配规则在程序中固定：双方队名只做大小写/重音/标点规范化，不进行人工猜测或模糊匹配；来源国家一致、UTC开球±60分钟，要求唯一历史比赛ID。**赛果不得参与候选ID选择**，匹配完成后才对照比分结果和Phase3目标标签。62场遗漏不按结果或赔率选择性填补。

## 3. 在完全相同175场上实际评分

国际市场`pin_open_home/draw/away`三项十进制赔率先取倒数并按三项之和归一化（去水）；网站`fair_prob`仅作非独立敏感性对照。

| 模型/来源 | 同场N | Log Loss↓ | 3类Brier↓ |
|---|---:|---:|---:|
| 国际市场第一份记录价格去水 | 175 | **0.998770** | **0.597135** |
| 网站自带fair概率（非独立） | 175 | 0.998771 | 0.597136 |
| EV-Lab联赛Poisson | 175 | 1.044675 | 0.630875 |
| EV-Lab Elo/Davidson | 175 | 1.060829 | 0.641180 |
| 全局历史频率 | 175 | 1.055318 | 0.635808 |
| 联赛历史频率 | 175 | 1.058833 | 0.636591 |

市场概率与Poisson相比，在本样本Log Loss低`0.045906`，Brier3低`0.033740`。用19个实际含匹配比赛的UTC日期配对、固定随机种子20261103做3,000次日级bootstrap，`market Log Loss - Poisson Log Loss = -0.0459057`，名义95%区间`[-0.0803006, -0.0074528]`。

**这只说明本批175场历史样本中市场定价的概率评分更好。** 由于样本短、11类联赛、62场无法匹配且没有独立赛前报价证明，不可把名义区间解释为长期市场优势，更不能据此计算可交易EV、CLV或真实ROI。

## 4. 真实复跑与证据根

正式可复用程序`tools/task0051_market_overlap_audit.py`；反例测试`tests/test_task0051_market_overlap_audit.py`。

只读原始数据与逐场评分在非Git目录：`E:\WebCodex-Workspace\EVLab-Data-Backups\phase3-tipsaudit-pilot-20261103\`。

- 第一次：`task0051-summary.json`与`task0051-details.json`；
- 重新运行：`task0051-replay-summary.json`与`task0051-replay-details.json`；
- 两次摘要逐字节相同，SHA256：`5aa250219ece0ac9e39d16f9ac849fb9c5cdda0c6f7fe05452327c1dcccb2bd4`；
- 两次逐场明细逐字节相同，SHA256：`7642d1af855de118d2a3e6323020b8e6187ed1d17dbcc095b29350a4c9d30e46`；
- 反例测试13项通过，全仓`488 passed`。

## 5. 阶段决定

**接受负结果：**Poisson/Elo在此前2.6万场回顾性比赛中优于简单频率，并不意味着能超越国际赔率。本次175场直接对照反而显示国际市场去水概率表现更好。

本阶段**工程与探索实验ACCEPT**；独立PIT市场报价比较与正EV判定维持**NO-GO**。优先建设/取得实际赛前带时间戳的同场赔率证据，扩大时间覆盖，再检验模型与国际市场的关系。不要以本样本制造收益故事。现有云端、Windows自动任务和独立14/任9项目均未改动。
