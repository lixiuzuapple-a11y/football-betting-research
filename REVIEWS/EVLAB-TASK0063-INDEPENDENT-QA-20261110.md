# EV-Lab TASK0063｜独立 QA：官方赛程 × 国际赔率跨源身份预检

**2026-11-10。可核验的真实来源分母 ACCEPT；正式同场市场身份与 PIT 仍 0/NO-GO。**

- [x] 通过 WebCodex 只读 SSH 核对腾讯云原有官方 collector 和赛前/评分 timer `active`，未重启或改变生产服务。
- [x] TASK0045 运行中的原始官方 gzip 是从 SQLite `ok` 接收记录的固定 SHA 定位并下载；本地解压独立得到 `3480202c716ad1027a603c5dd834f10c566df873789b71846e9828d30dbc0885`，官方 `8` 个唯一 `matchId`，未误报整个运行 epoch 完成/封存。
- [x] 正式 `qualify_fixtures` 使用冻结 14 联赛及受检 143 官方身份，得到 `league_not_approved_for_forward_model=8`，没有新前向许可比赛。
- [x] 重用 TASK0062 已有法甲 API 原始 SHA `78c1f19a29b0385f80dac776d0b66e932d038d9dc87ed301ef9cd4e3b454f571`；对比真实 `18` 场（另一个时点），没有为了研究结果消耗新增的 API 额度。
- [x] 原始 CSV 自行重新计算中心主表 `501`、14 联赛有历史成员记录的 `480`、旧有严格批准但无 14 联赛历史成员记录的 `21`；143 已批准体彩身份中，122 位于这 14 联赛历史关系中。已加口径勘误，不修改 SHA 锁定源表。
- [x] 不依赖摘要生成过程，重新读取本地原始 gzip、原始 API JSON、v1 身份表核验 SHA、8/18 分母及 4 条候选供应商事件 ID、双方原文与官方 ID 均一致。
- [x] 四条仅为两队英文名称与已核验身份的候选，没有官方比赛 `matchId`，`independent_provider_event_official_match_id_bridges=0`，未被写入正式许可表、前向预测、真钱下注或历史回测。
- [x] 原始证据和账户 `.env` 仍被 Git 忽略；只推送零密钥、无原始报价价格的研究摘要。

**最终：ACCEPT 冻结的来源分母/负面交集结论和候选队列；REJECT 提升候选到正式同场事件、CLV 或正 EV。**
