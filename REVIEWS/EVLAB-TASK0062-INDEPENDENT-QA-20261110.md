# TASK0062 独立 QA｜免费 The Odds API 来源资格

**2026-11-10，结论：source transport/schema PARTIAL ACCEPT；PIT market-to-model admission NO-GO。**

- [x] 与原 `research/TASK-0009_REFERENCE_SOURCE_QUALIFICATION.md` 和 TASK0061 门禁比对，未新设第三套采集管线、定时器、登录账户或付费操作；真实 API 凭证只在 Git 忽略 `.env` 中。
- [x] API 赛事目录 HTTP200、42 soccer keys、11/14 目前可见；本次 /sports 额度扣费 0。缺失 3 个 key 只代表这次观察，没有永久性结论。
- [x] 真实法甲 API HTTP200、单次扣费 1，接收于 2026-11-10 08:39:37 UTC；原始字节 SHA256 `78c1f19a29b0385f80dac776d0b66e932d038d9dc87ed301ef9cd4e3b454f571`。完整原始 JSON 保存在被 Git 忽略的 `data/raw`，没有钥匙或带钥匙 URI 提交。
- [x] 第二种语言/实现从原始 UTF-8 JSON 和收件回执独立重算，原 SHA 相符、18 唯一法甲赛事、20 家公司、18 场 Pinnacle、244 条无坏价的完整主胜/平/客胜，244/244 `last_update` 距收件不超过 15 分钟。
- [x] 独立复核发现 PowerShell 日期自动解析产生虚假 +8 小时时差；改用源 JSON 字符串的 UTC-aware ISO8601 解析，得真实 0.12–1.34 分钟、Pinnacle 0.39–0.40 分钟及距离开球 251–467 小时。原失败计算不计入报告。
- [x] 精确别名候选联接：法甲 18 场中 10 场两侧唯一匹配历史 HF 原文，4 场两侧名称同时落在已批准旧体彩身份范围；仍然 **0 独立批准的 provider↔official 赛事事件桥**，未自动晋升。
- [x] 现有同场同时点严格门禁测试 16 passed；全仓 `python -m pytest -q` 592 passed。
- [x] 结论清晰隔离：实时供给和相对新鲜的市场观测 ≠ 供应商原始修改时刻 ≠ 模型冻结前 Git 锚 ≠ 可交易市场价 ≠ 正 EV。

**QA 裁决：PARTIAL ACCEPT 真实数据源、报价完整性和可用更新时间；REJECT 把该样本作为模型冻结时点的市场价格。** 零付费不变，不启动持续采集，不影响原前向 N=3 或 14/R9。
