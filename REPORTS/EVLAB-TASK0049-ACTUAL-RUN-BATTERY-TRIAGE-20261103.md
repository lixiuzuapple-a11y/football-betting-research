# EV-Lab TASK0049｜2026-11-03真实前向运行与计划任务诊断

## 证据范围与禁忌
本报告基于当天Windows真实任务状态、实际Scheduler事件、官方原始采集、云端systemd健康状态、Git记录与测试输出。没有新增有效Git锚定的赛前预测，也没有市场赔率、CLV、正EV或实盘结果。

## 1. 今天11:15实际失败
- 任务：EVLab-TASK0046-DailyForward；11:15最后结果Windows十进制3221225786，即十六进制0xC000013A（进程收到中断/终止）。
- 截至15:06原Scheduler FINISHED日志与对应运行journal**均无**11月3日11:15记录。原PowerShell脚本只在finally写记录，遇到外部进程终止无法留下开始痕迹。
- 旧任务设置：DisallowStartIfOnBatteries=True、StopIfGoingOnBatteries=True；Windows当时Win32_Battery报告BatteryStatus=1（正在放电），电量约43%。
- 15:10、15:15手动Start-ScheduledTask触发状态为Queued，没有Python/原始采集；开启Scheduler Operational日志后可查Event 325（实例排队），不能把LastTaskResult=0理解为任务完成。
- **边界：**以上证实当前电池供电会阻碍排队任务，但不能反推11:15的全部终止因果。

## 2. 改动与真实恢复尝试
- 工具：tools/task0044_forward_orchestrator.py 的NO_NEW_FREEZE新增原始官方比赛数量、交叉身份资格数量、模型推断资格数量及分项拒绝原因，不改变算法、不调整准入。
- PowerShell wrapper deploy/Run-Task0046-DailyForward.ps1 在入口即写STARTED，正常退出或可捕获失败时写FINISHED和退出码；硬中断时留下无FINISHED开始记录。
- 专项测试43 passed，完整代码测试475 passed，PowerShell脚本语法和git diff检查通过。
- 实际**直接调用同一正式PowerShell脚本**在15:13:54—15:14:02北京成功，FINISHED exit0。不可覆盖运行journal：
  `E:\WebCodex-Workspace\EVLab-Data-Backups\task0046-forward-20261031\journal\run-20261103T071354827011Z-58af2682.json`
- 该真实源采集观察21场，21场均被`league_not_approved_for_forward_model`排除：crosswalk_qualified=0，model_qualified_before_dedup=0，no new Git freeze；原始来源SHA256：
  `7a6d46c83541521fce4bc15dba7b68bf66b94d200e11a4b579cc20c105282293`。
- 结果解释：**这天0新前向样本首先是官方赛程在当前仅获批的挪超/法甲两个联赛外**；不是该源21场都因队名匹配失败。不得凭此要求放松资格边界。

## 3. 电池策略与剩余故障
- 新版本化操作：`deploy/Set-EVLab-WindowsTaskPowerPolicy.ps1`；真实运行后两个任务（TASK0046 11:15、TASK0048 18:30）均验证DisallowStartIfOnBatteries=False，StopIfGoingOnBatteries=False，且Principal/Action/Triggers保留原值。
- 修复后TASK0046原来Queued状态变Ready，15:19再次手动启动确有真实Task Scheduler事件100/129/200（powershell.exe动作启动），但在15:19:27事件201返回**3221225786 / 0xC000013A**；Scheduler实例事件102标记终结。
- 该次PowerShell入口的STARTED记录存在，**没有FINISHED或新的journal**。因此调度进程的后续异常中断仍未定位，**不能宣称无人值守运行修复验收**。
- 明确排除一种错误归因：修改电池条件解除Queued，但不能解释或修复全部0xC000013A。后续需在PowerShell preflight/Git/Python阶段增加受限阶段标记，检查Windows终止来源及任务主体环境；或独立论证云端长期运行路径，不得跳过Git前向时点门禁。
- Windows Task Scheduler Operational日志已启用以保留事件。TASK0048当晚18:30自动运行尚未发生；其电池设置修改成功，**不等于已经完成真实评分验收**。

## 4. 云端不受影响
- Nov3约15:14北京时间检查：evlab-task0045-official.service和health.timer active，SQLite quick health=OK，来自新epoch的119次原始源捕获全部校验通过，健康状态OK，约40GiB空间。
- 主仓主线无任9、14场代码改动，之前TASK0044两场真实评分结果不变。

## 5. 结论与下一研究门槛
1. 归因和审计问题：改善完成；官方真实捕获及无合格结果可复核。
2. 源覆盖问题：仅两个获批联赛、35条冻结身份样本太窄；应优先在独立新数据与完整身份验证下扩大**可用赛事范围**，不可从全部21场中直接造新合格预测。
3. Windows无人值守问题：调度仍外部终止，**REJECTED / 需继续修复**。不应依赖其来保证每日前向样本。
4. 当前不具备市场收益正EV验证证据。

研究代码提交：`51865d96b435d768ee8f9b708dd070f8a1658e9a`；电源策略操作脚本提交：`ffbffefd7eb08b5e235bf739e63f8ca07f43eeb2`。
