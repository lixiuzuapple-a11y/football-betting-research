# EXPORT_打包下载 — 入口索引

> **用途**：把 `/workspace` 内的研究资产**分卷压缩**，便于一次性下载到本地。
> **打包时间**：2026-09-22 08:2x
> **覆盖范围**：`/workspace` 全部文件，**不含 `backups/`**（778M，与 `data/` 高度重复）
> **覆盖率**：**928 / 928 文件 = 100%**（已用 `comm` 比对核验，零遗漏）

---

## 一、怎么用

1. 打开 `MANIFEST.md` → 查看每个包的**大小 / 文件数 / SHA256 / 内容明细**
2. 依次下载需要的 `.zip`
3. 解压后**目录结构已保留**（解压出来就是 `REPORTS/`、`data/`、`scripts/` 等原样结构）
4. 校验完整性：`sha256sum *.zip`，与 `MANIFEST.md` 中记录对比

---

## 二、19 个分卷一览

| # | 包名 | 大小 | 文件数 | 内容 |
|---|---|---|---|---|
| 1 | `01_交付物_REPORTS.zip` | 0.1MB | 5 | **本轮 REV-3 交付物**（主报告 + 4 份配套） |
| 2 | `02_顶层研究报告_md.zip` | 0.5MB | 25 | 顶层研究报告 `.md` |
| 3 | `03_顶层报告_html.zip` | 0.1MB | 8 | 顶层报告 `.html` |
| 4 | `04_顶层其他_xlsx_py.zip` | 1.4MB | 2 | `模拟盘跟踪表.xlsx` + 交接脚本 |
| 5 | `05_脚本_scripts.zip` | 1.4MB | 241 | 全部研究脚本 |
| 6 | `06_结果_results.zip` | 6.5MB | 46 | 实验输出 |
| 7 | `07_日志_logs.zip` | 0.0MB | 23 | 运行日志 |
| 8 | `08_data_采集原始_odds.zip` | 5.6MB | 2 | 采集原始赔率（最大两表） |
| 9 | `09_data_历史与赛程.zip` | 11.3MB | 5 | `hist_v2` / `fb_*` / `jc_ttg_ts` |
| 10 | `10_data_lambda与派生.zip` | 8.6MB | 6 | λ 拟合与反解派生 |
| 11 | `11_data_clean目录.zip` | 3.3MB | 2 | `data/clean/` |
| 12 | `12_data_historical_160.zip` | 6.8MB | 189 | football-data 历史包 |
| 13 | `13_data_fd_各赛季.zip` | 4.3MB | 102 | football-data 各赛季 |
| 14 | `14_data_快照与推荐.zip` | 0.9MB | 89 | 快照 / 推荐 / 预测 |
| 15 | `15_data_竞彩清理与结果.zip` | 0.8MB | 6 | 竞彩清理与结果表 |
| 16 | `16_data_okooo历史系列.zip` | 0.9MB | 7 | okooo 历史系列 |
| 17 | `17_data_实验中间产物含e54.zip` | 1.1MB | 7 | E 实验 join/pairs 中间产物 |
| 18 | `18_data_其他派生素材.zip` | 0.7MB | 156 | 其余派生散件 |
| 19 | `19_补充遗漏文件.zip` | 0.0MB | 7 | 补漏（含隐藏文件 `.last_report`） |

**合计 19 包 / 54.6MB / 928 文件**

---

## 三、重要说明

### ① `backups/` 未包含

`backups/` = **778MB**，占 `/workspace` 总量约 70%，且内容与 `data/` 高度重复（5 个历史快照）。

本打包**有意排除**它：
- 若纳入，包数会膨胀到 70+ 个，且大小严重失衡
- 冻结基线通常不需要历史快照

> ⚠️ **如需包含**，请明确说明，可按同样口径另行分卷。

### ② 打包为纯只读操作

- 源文件**未移动、未删除、未修改**（仅 `cp` 复制后压缩）
- 未触碰 `data/`、`scripts/`、`results/`、`backups/`、`logs/` 任何内容
- 未重启任何采集进程

### ③ 这与 TASK-0003 无关

本目录是**临时导出**，**不是** TASK-0003 要求的 staging 目录。

TASK-0003 指定的 `E:\OneDrive - Swire Properties Limited\football-betting-legacy-staging\`
位于**用户本机**，本沙箱为 Linux 隔离环境，**不存在 E: 盘 / OneDrive 挂载**，无法写入。
详见主报告 §0.2 及 TASK-0003 的 blocker 记录。

---

## 四、相关链接

| 文件 | 说明 |
|---|---|
| `MANIFEST.md` | 各包 SHA256 + 内容明细 |
| `../REPORTS/INVENTORY-20260921-01_竞彩足球研究资产只读盘点.md` | 主报告（REV-3） |
| `../REPORTS/REVISION_NOTES.md` | 修订说明（REV-1/2/3） |
