# EV-Lab PHASE-1：官方数据工厂实际整库验收（2026-10-26）

## 结论

**ACCEPT：阶段一「离线统一官方数据工厂」已用真实两批原始数据完整运行，并经独立数据库审查。**
**NOT VERIFIED：云端持续采集、自动恢复与告警；多赛季大样本模型平台；前向模型预测；赔率真实成交；正EV或盈利。**

不再按个别球队反复修补。将历史采集数据按真实接收时间、原件哈希、盘口状态和市场更新时间自动组织成可复现的研究数据库。

## 输入、输出及已验证证据

输入（均只读，原始副本位于 Windows E盘）：
- `E:\WebCodex-Workspace\EVLab-Data-Backups\official-20261018\task0024-official-20261010`
- `E:\WebCodex-Workspace\EVLab-Data-Backups\official-20261018\task0025-official-20261015`

执行指令：
```text
python -m tools.phase1_data_factory --root <TASK0024-backup> --root <TASK0025-backup> --out-db <new-root>/candidate_quotes.sqlite3 --out-summary <new-root>/quality_summary.json
```

输出：
- `E:\WebCodex-Workspace\EVLab-Data-Backups\phase1-data-factory-20261026\candidate_quotes.sqlite3`
- 同目录 `quality_summary.json`

本地原始源和衍生 SQLite 大文件均不上传普通 Git；Git 只保存源代码、测试、可复现流程和阶段统计。

### 整库结果（无抽样）

| 项目 | 实际计数 |
|---|---:|
| 源数据库总捕获记录（包括失败/空响应） | 9,522 |
| 验证成功的独立原始压缩响应哈希 | 9,519 |
| 正常HTTP原始响应 | 9,515 |
| 空响应 | 4 |
| 传输错误 | 3 |
| 采集批次 | 2 |
| 不同比赛 | 169 |
| 比赛快照观察 | 234,340 |
| 五市场总观察记录 | 1,163,746 |
| 研究级初始/有效变价候选事件 | **1,727** |
| 使用的提供方报价年龄门槛 | **6小时**（研究假设，非成交证明） |

事件按五市场分布：

| 市场 | 初始有效候选 | 有效变价候选 | 合计 |
|---|---:|---:|---:|
| HAD 胜平负 | 149 | 240 | 389 |
| HHAD 让球胜平负 | 157 | 242 | 399 |
| TTG 总进球 | 154 | 177 | 331 |
| CRS 比分 | 152 | 132 | 284 |
| HAFU 半全场 | 152 | 172 | 324 |
| **合计** | **764** | **963** | **1,727** |

这是经过旧状态机约束及新6小时有效年龄条件后得到的**报价事件**，不是独立比赛数、同等独立样本，也不是实际可以成交的下注机会。

### 独立工程验收

- `python -m pytest -q tests/test_phase1_data_factory.py`：**7 passed**。包含跨源乱序合并、重复报价抑制、原始哈希破坏、同ID球队身份变化拒绝、陈旧报价/停售/未来时间过滤、赛后/非有限赔率过滤、重复matchId/覆盖根目录保护。
- `python -m pytest -q`：**374 passed**，此前367项保持通过。
- 完整构建程序完成（exit 0）；`partial_scan=false`。
- 另用**独立只读 SQL 查询**验新库：`PRAGMA quick_check=ok`、`PRAGMA foreign_key_check` 0错误；`quote_candidates`=1727、`source_captures`=9522、`fixtures`=169；赛后候选=0，非法event_kind=0。
- 输出为独立新根，源文件及历史SQLite不修改，且输出同名文件存在时拒绝覆盖。
- GitHub 不包含赛果收益、模型假阳性和原始三方受限文件。

## 云端状态与本阶段明确边界

2026-10-26 北京时间，本地 WebCodex 和云端 SSH 可用；远端主机约50GB磁盘、40GB可用，`/home/ubuntu/evlab-data` 原历史证据目录约354MB。旧多项服务当前inactive，云端`systemctl list-unit-files` 只确认旧TASK0005/0006服务与健康timer模板，未出现运行中的正式新产线。旧TASK0024是明确**七天有界**任务，不得仅凭不运行归因当前采集器崩溃。

因此目前**不是**“云端自动持续采集已经验收”或“规模化模型已上线”。本阶段提供一个可审计的真正可运行的统一数据处理环节，而非新部署的守护服务。

## 阶段下一步（面向规模化而非单场修补）

1. 先在新根用有界官方采集的固定源版本跑新的真实赛前时间窗，恢复定时监测，做开机、失联、停售、停机等故障工况验证，验收后再讨论长时间运行。不能悄悄重启旧历史根。
2. 将 `quote_candidates` 视为独立市场观测事件流，正式连通赛前训练特征及版本化模型API；比赛ID冲突应该在后续版本按隔离统计处理，不能触发人工逐队持续修复。
3. 多模型同场样本外评分仍以市场去水概率为强基准。真实前向预测必须在开赛前冻结；没有外部授权且时点可靠的Pinnacle数据，不宣称完成Pinnacle真实CLV。
4. 对模型研究的绩效分开按训练/验证/测试窗口裁决，拒绝在旧169场上大规模寻找赢利参数。

**本阶段仅就数据工厂 ACCEPT，其他目标仍需阶段验收。**
