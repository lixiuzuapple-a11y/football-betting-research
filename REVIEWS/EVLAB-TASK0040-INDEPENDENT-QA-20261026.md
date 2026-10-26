# EV-Lab TASK-0040 — 独立 QA / 2026-10-26

## 审查对象及裁决
- 基线：main `358973a1bb0c268b0ffe554429fa01ebcd187b38`（2026-10-26 11:57:37 +08:00；检查时与 origin/main 同步，初始工作区 clean）。
- 本阶段裁决：**ACCEPT（官方赛前来源快照、原始证据一致性、严格准入工具）**；**NOT VERIFIED（腾讯云持续采集/服务故障根因与数据库最新捕获时间）**；**NO-GO（独立预测表现、正 EV、实盘投注或生产部署）**。
- 仅对当前预先冻结的两个有效官方 HAD 市场基准做验收，**不把市场去水概率当作独立模型结果**。

## 我方独立复核（非执行人自述）
1. WebCodex runtime ready；5/5 注册项目 online，`football-betting-research` 可用；Git main = `358973a`，origin/main 同步。
2. `python -m pytest -q tests/test_task0040_new_window_gate.py`：8 passed。
3. `python -m pytest -q`：367 passed (6.48s)。
4. 只读打开 E 盘 `EVLab-Data-Backups/task0040-new-official-window-20261026`，核实两份原始 Sporttery 响应文件均为 52,798 字节；逐份运行仓库 `tools.task0040_new_window_gate.run(manifest)`，独立交叉校验 `research/task0040_new_official_window_freeze_20261026.json` 中的每次原始 SHA256、各自 manifest SHA256、matchId 顺序、4 场总数和每次 2 场严格通过：**PASS**。
5. 两次接收时间：2026-10-26 03:49:44.926854 UTC、03:52:49.405926 UTC；原始文件 SHA256 相同：`4079741dcbd9f9dd7ef65bd241da9f0592988b2bdb33e62aee0cb04857331457`。
6. SSH 仅做一次新的只读连接探测：`ssh -o BatchMode=yes -o ConnectTimeout=8 -o ConnectionAttempts=1 -o ServerAliveInterval=3 evlab-cloud date ...`，以 exit code 255、`Connection closed by [server] port 22` 结束。未取得云端 systemd/journal/SQLite 新证据，不擅自归因为 collector 崩溃、磁盘满、SSH 限流或数据停止。
7. 未重启服务、未写云端、未更改 E 盘原始源、未制造赛果或赛前模型预测。

## 关键防错
- 4 场数字 HAD 可见，严格 HAD 接受 **2/4**；其余 2 场非零 HAD flags 必须拒绝。
- 接受样本 2042242 的 provider 赔率更新距接收约 50.06 小时，报价有明显陈旧风险；该来源状态本身**不能**证明下注可执行。
- 仅两次 HTTP200 且 payload 相同，不代表持续云端采集健康，也不代表盘口连续采样、市场价格刷新或 CLV 可计算。
- 最新云端捕获点及旧 failed units 的确切 Exit/Result 仍待登录后只读核查。特别是有时限历史任务正常停止与异常失败必须区分。
- 未来比赛尚未结束；本次没有模型事前冻结预测；没有收益率或下注记录。不可生成 BUY。
- 原始第三方源仅存本地 E 盘并用摘要证明存在；GitHub 只记录派生账本和复核，不上传原始文件。

## 下一独立验收门槛
1. **云端连通性**：先从腾讯云控制台/VNC 或恢复后的受控 SSH，只读取得服务 `ActiveState`/`Result`/`ExecMainStatus`、最近 journal、磁盘容量、数据库及其最新捕获时间，并确认旧任务是否按时到期。记录完整 UTC 时间与受审 unit 名称。
2. **采集重建**：在故障定性且 Owner 批准后，仅在**全新数据根**启动符合采集上限、官方来源、哈希和时间戳要求的新任务；禁止覆盖旧封存根、拿旧样本冒充新样本。
3. **真正前向评估**：独立模型须在开赛前冻结输出、记录模型版本/源时点，赛果出现后由另一流程盲评；同场市场去水基准、有效下注价及成本必须独立留证。
