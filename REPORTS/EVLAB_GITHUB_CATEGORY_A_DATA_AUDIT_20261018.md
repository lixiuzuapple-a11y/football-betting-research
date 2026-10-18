# EV-Lab｜开源项目逐类实证：第一类 A — 数据源与数据适配器（2026-10-18）

## 本阶段结论
**A 类研究可有条件 ACCEPT（独立数据源证据已验证）；目前不建议整包安装任何第三方抓取框架。** 这不是对全部18个项目的总体验收，其余 B/C/D 三类均标明 PENDING。四类的唯一分类台账见 \`research/github_category_decision_20261018.json\`，数量分别 A=4、B=5、C=4、D=5，无重复无遗漏。

评估六个维度：①实际数据需求与覆盖；②原始仓库源码和许可；③独立源访问与字段；④时间性/PIT；⑤球队身份匹配与否证；⑥安装维护成本及边际收益。证据不充分处判“保留/拒绝”，不盲从 GitHub README。

## 主要真实发现
独立只读原始快照位置：\`E:\WebCodex-Workspace\EVLab-Data-Backups\github_category_A_evidence_20261018\`。共9次 HTTP/HTTPS 探针，**8次200，1次失败**。源响应字节存为 \`*.raw\`，附 \`SOURCE_PROBES.json\` 中各时间戳、SHA256、URL、状态及实体计数。代码 \`tools/audit_category_a_data_sources.py\` 可复算来源SHA256、按官方169场赛程校验 ESPN 严格匹配并交叉验证最终比分，证据输出 \`CATEGORY_A_JOIN_AUDIT.json\`。

### 四仓库逐项裁决

| GitHub仓库 | 源码/许可、可运行证据 | 已实测边界 | 决议 |
|---|---|---|---|
| [probberechts/soccerdata](https://github.com/probberechts/soccerdata) | Apache-2.0，\`soccerdata/espn.py\` SHA \`6401808a47f7f30ee33bd492bb78f1aaf9631c89\`，\`clubelo.py\` SHA \`e20eba86...\`，\`understat.py\` SHA \`24c17f...\`；源 \`pyproject.toml\` 基础依赖含 SeleniumBase、pandas、lxml 等，整体较重。用源码声明的 ESPN 公共接口单独实测，而不是假称原版软件已运行 | ESPN 10/10英超6场全部完赛，10/18查询4场其中3场下半场1场未开始；ClubElo \`http://api.clubelo.com/2026-10-10\` HTTP502；Understat 2026英超页面HTTP200但本次未验证内含 xG 结构/历史可用性 | **有限采用 ESPN 数据源参照与身份核验方法；拒绝当前安装整个 soccerdata 栈及声称 ClubElo 已接入** |
| [openfootball/football.json](https://github.com/openfootball/football.json) | CC0-1.0，README明确 JSON 每日生成但底层 Football.TXT 并非每日自动更新 | 26/27英超380日程仅45场 FT，比对德甲306日程仅33场FT；二者最近有比分的比赛停在2026-09-20；2026-10-10开始的日程并无成绩 | **只保留作历史/赛程辅助；不进入当期赛果或即时特征** |
| [hudl/open-data](https://github.com/hudl/open-data) | StatsBomb 公共赛事、赛季、比赛事件、阵容接口；README要求署名和logo | 赛事目录80个赛季条目，无名称包含2026的赛季；指定2023/24德甲比赛 JSON 真实包含34场，但与 EV-Lab 当期比赛不同 | **仅作事件分析方法及老赛季研究的隔离材料，不列入当前169场队伍实时源** |
| [martj42/international_results](https://github.com/martj42/international_results) | CC0-1.0；原版README写49,459场截至2024，实际 \`results.csv\` 当前HTTP200、**49,945**条且全部有数字比分、最新日期 **2026-10-06**，说明README已滞后，需要相信冻结原件而非简介 | 内容为男子国家队成人国际比赛，包括部分加时比分，不是俱乐部比赛；169场28种赛事大多为俱乐部 | **保留国家队后续研究，当前 EV-Lab 169场不接入** |

### 一次真实跨源 ID 负对照与正对照（soccerdata → ESPN）
仅在固定的日期2026-10-10和10-18各检索英超 ESPN 原始 scoreboard 响应；从 TASK0024/TASK0025 原始只读备份的 SQLite，每隔45次成功响应抽一个 gzip，按 \`matchId\` 去重得到169个原始比赛身份。匹配必须同时满足：
1. 英超赛事；
2. 亚洲上海时区转换后的 **开赛日期和秒级时间相等**；
3. **主、客队双方英文缩写分别相等**；
4. 官方 \`matchId\` 对应唯一 ESPN \`event.id\`，不得仅按同一开赛时间合并多场；
5. 仅当 ESPN状态是 \`STATUS_FULL_TIME\` 或 \`STATUS_FINAL\` 且双方得分为非负整数，才与 EV-Lab 已保存官方完赛结果比较。

总计10条 ESPN 事件：**3条满足严格身份联接**，其中 **2条双方官方来源最终比分完全相同**：
- \`2041876\` 切尔西 vs 伯恩茅斯，体彩5:1 / ESPN5:1；来源 ESPN \`401878775\`。
- \`2041875\` 伊普斯维奇 vs 富勒姆，体彩2:1 / ESPN2:1；来源 ESPN \`401879265\`。
- \`2042058\` 伯恩茅斯 vs 桑德兰两队身份匹配，但 ESPN记录时仍处下半场，**不允许当作赛果标签**；其余7个 ESPN event 因目标采集集不含或双方缩写不同而未严格联接。

**不把这3例夸成169场全部 ID 打通。** 例如同时间有三场英超：阿斯顿维拉官方缩写 ASV、ESPN AVL；布伦特福德官方 BRN、ESPN BRE；上述本来确有比赛，但严格规则拒绝这种别名不匹配。若将来需要晋级，应建立逐队有来源的官方跨源身份表而非直接把缩写“近似”当作同队。不同比赛同一开球时点必须触发反例，不能仅按时间归一。

### 依赖/成本与真正复用内容
\`soccerdata\` 全包有浏览器 SeleniumBase 和多依赖；当前要的只是一个可重复请求的 ESPＮ JSON API，使用Python标准库即可，不需要部署重量级框架到既有 2GB 云机。ESPN 的接口可访问 ≠ 我们拥有稳定的正式商用数据授权；不得绕登录/人机检测或许诺永续服务。本轮只做必要的少量公开请求和离线比对。

新增加的 \`tests/test_category_a_data_sources.py\` 通过自造同时间两场、颠倒主客队、错开一分钟、比赛未结束、响应格式坏掉等负对照。独立 \`CATEGORY_A_JOIN_AUDIT.json\` 和 \`SOURCE_PROBES.json\` 保存在 E 盘证据目录；GitHub 只保存实验代码、测试、分类台账和报告。

## 继续下一类的门槛
**A 类已完成，可进入 B 类（成熟统计/概率模型5项）。** B 类应先核对许可证及原版算法输入，优先为 \`penaltyblog\` 与 \`callumfm/dixon-coles\` 做真正原版受控运行，用已保存历史数据与冻结未来赛季，比较不使用赔率的概率和市场；\`theopenmodel\` 与 \`yukunai\` 要检查 ClubElo不可用时是否有可信退化路径，\`kenRedco\` 原版测试只做来源后再晋级。不得把 A 类的2场交叉赛果一致当成 B 类模型得到独立优势。

**阶段裁决：A类 ACCEPT（研究审计完成）；生产数据层只批准 ESPN 小范围只读候选，不批准自动采集/策略上线。**
