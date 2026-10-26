# EV-Lab Phase2 — Independent QA and acceptance boundary

2026-10-26。对阶段性可检验成果独立复核。

## 审计事实
1. 远端 `/home/ubuntu/task0024_collector.py` SHA256 与 `eb1099a:tools/task0017_official_only.py` 一致，现有旧数据目录保持不动。
2. SSH真实部署新transient服务，首笔采集 `ok`/HTTP200/4场，旧目录与新目录分离，SQLite `PRAGMA quick_check=ok`。06:18 UTC前累计10条采集及多次独立2分钟健康记录均 `OK`。
3. 新模型输入只有在当次预测创建前已发生、来源已核验的135条历史比分，所有训练比赛日期截至2026-10-18；赔率扰动反例测试确认独立概率与ID不受赔率变化影响。
4. 未来真实比赛4场已于2026-10-26 14:16:58 CST一次性create-only冻结，首场开赛2026-10-27 02:45 CST；原始源manifest和冻结文件SHA均已固定在提交报告。
5. `phase2_forecast_lab score` 有真实接口与对抗性单测，但尚无新赛果，不允许声称“模型准确率”。
6. `pytest` 新增7项和全仓381项通过。

## QA裁决
- **Cloud: QUALIFICATION STARTUP ACCEPT**, bounded 48h operation PENDING.
- **Forecast: BASELINE FREEZE ACCEPT**，固定历史弱基线，4份事前记录，市场合格参考2份。
- **Market/sports-betting financial result: NO-GO**。同场同时间点赔率尚未证明；没有Pinnacle真实价、没有实际下注成交或未来评分。
- **Always-on production: NO-GO**。systemd-run transient不是持久化部署；2分钟巡检仅写远端日志，无人值守主动通知未配置。
- **Full multi-model research lab: PARTIAL**。通过真实Forecast Contract，但未把外部Dixon-Coles/Elo正式编排为持续运行的生产pipeline。

下一阶段要把已有成熟算法与未来可用训练数据自动衔接，并完成新采集生产服务的多日稳定性与自动评分，而不是重新纠缠几个球队名。
