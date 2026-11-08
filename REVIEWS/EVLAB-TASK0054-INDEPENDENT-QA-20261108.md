# TASK0054 独立QA（2026-11-08）

## 核验判据

- [x] GitHub deploy key仅限私有EV-Lab仓库，云端有独立完整Git工作树、与origin/main一致；真实push新临时分支、校验提交SHA和远端删除均通过。
- [x] 真实腾讯云`systemd`的前向服务和赛后评分服务分别执行exit0，有`STARTED/FINISHED`原始日志；不只是直接运行Python。
- [x] 两个基于`systemd-run --on-active`的真正时间触发canary分别驱动相同正式service，结束退出码0。
- [x] 官方数据、球队身份/历史源SHA及Git干净工作区校验保留原TASK0046代码；实际捕获25场中已提交的`2042640`被正确去重，零重复Git提交。
- [x] 真实赛前Git锚`632aced`源freeze已在云评分根按create-only登记；原TASK0048识别Git锚并返回`WAIT_KICKOFF_PLUS_THREE_HOURS`，没有提前获取赛果。
- [x] 两个正式云timer已执行`enable --now`，独立读回`enabled/active`；下一次触发为北京时间11月9日11:15及11月8日18:30。两项services的有界重试配置实际读回`Restart=on-failure/RestartUSec=5min/StartLimitBurst=3`。
- [x] **云端两项均active之后**，Windows两项原计划任务XML先备份并记录SHA，再`Disable-ScheduledTask`；随后两项均读回`Disabled`。保留旧任务和所有历史日志，没删除。
- [x] 云端TASK0045原官方连续采集服务和健康timer持续active/OK，SQLite正常；未触碰14场/任9独立项目。
- [x] 本次回归`509 passed`，Git中没有私有SSH key或GitHub个人Token，原评分、赛前时间及下注禁止规则未放宽。

## 尚未通过的进一步可靠性闸门

- [ ] 第一次真正每天正式timer无人值守运行（11月8日18:30评分、11月9日11:15前向），目前只能确认正式timer已启用和一次性canary成功。
- [ ] 11月9日后对比赛2042640完成至少开球后3小时的真实官方独立盲评。
- [ ] 重试故障注入、连续多日服务健康及Git冲突/断网恢复演练。
- [ ] 完整PIT国际市场赔率与真实CLV、统计学稳定正EV能力。

## 结论

**TASK0054 单一云端自动发布者工程切换：ACCEPT；长期稳定性：PENDING；正EV：NO EVIDENCE。**

本次成功把此前受Windows`0xC000013A`制约的本地定时执行责任迁到腾讯云，消除Windows与云端两个**已启用的自动发布者**同时存在的问题。但没有宣称旧Windows内部异常根因已解决，也没有把未来尚未发生的自动运行或盲评成绩伪称完成。
