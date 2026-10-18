# EV-Lab｜公开 GitHub、数据及论文搜索支线（2026-10-18）

## 研究目的与方法
复用 A 股项目的 RESEARCH_CAPABILITY_SYSTEM_v1 与 ENG21 审计纪律：问题定界 → Web/GitHub多语检索 → 仓库真伪/原版源码/许可 → 数据实时探针 → 反向证据 → 决定是否引入。GitHub 已连接账号确认 **18/18 候选真实仓库存在且未归档**；多项目读取具体原版源文件 SHA。OpenAlex 官方接口实测返回 DOI。源字段 E1=真实仓库或README；E2=原始实现文件核查；E3=本地程序实际请求公开源数据。E3 不等于跑通全部第三方工程、也不是其作者自评的独立复现。

没有在云服务器部署软件，没有安装大型爬虫或新模型，没有修改原始 EV-Lab 足球数据。A股项目已有的未提交工作文件保持原状，本支线只读检查。

## 我们真实169场的需求范围
从 TASK0024 和 TASK0025 备份通过每60份响应抽一份、按 matchId 去重，得到 **169场、28类赛事**。分布前列：意甲19、西甲18、英超17、欧冠15、德甲12、欧罗巴10、法甲9、荷甲8、巴甲6、亚冠精英6，以及瑞超/英冠/挪超各5。五大联赛合计 **75/169=44.4%**。因此只下载英超和五大联赛，不能解决绝大多数场次的外部历史特征。169场均有英文字母球队简称，例如 IPS、FUL，但是这些是缩写，不是与外部数据库共享的唯一球队ID；身份桥须显式、逐项核证。

## 18个 GitHub 候选分级（不是全部安装名单）
| [probberechts/soccerdata](https://github.com/probberechts/soccerdata) | P0 | E2 | 多源数据适配器，原版 ClubElo 源码已审 |
| [martineastwood/penaltyblog](https://github.com/martineastwood/penaltyblog) | P1 | E2 | Dixon-Coles/Poisson现成算法候选 |
| [dank0i/football-forecast](https://github.com/dank0i/football-forecast) | P0 | E2 | 反事实时间泄漏测试、市场对照；上游成绩未复现 |
| [alexander-quang-phan/football-match-outcome-prediction](https://github.com/alexander-quang-phan/football-match-outcome-prediction) | P0 | E2 | 赛后排名泄漏反例、平局召回报告 |
| [Hicruben/theopenmodel](https://github.com/Hicruben/theopenmodel) | P1 | E2 | 赛前冻结快照流程、Elo至Dixon-Coles |
| [OPaheimer/premier-league-predictor](https://github.com/OPaheimer/premier-league-predictor) | P0 | E2 | freeze/grade/ledger流程，但允许替换快照 |
| [kaspersgit/football-prediction-autoresearch](https://github.com/kaspersgit/football-prediction-autoresearch) | P3 | E2 | 训练特征含market_h等，不符合独立模型 |
| [callumfm/dixon-coles](https://github.com/callumfm/dixon-coles) | P1 | E2 | 较小的DC实现可对照 |
| [openfootball/football.json](https://github.com/openfootball/football.json) | P2 | E3-源访问 | CC0比分、赛程；十月比分更新滞后 |
| [hudl/open-data](https://github.com/hudl/open-data) | P2 | E3-源访问 | StatsBomb事件数据，非169比赛即时历史源 |
| [ML-KULeuven/socceraction](https://github.com/ML-KULeuven/socceraction) | P2 | E1 | 球员事件SPADL/VAEP，不是比分来源 |
| [kenRedco/football-predictor](https://github.com/kenRedco/football-predictor) | P2 | E1 | walk-forward与Poisson+XGBoost候选 |
| [yukunai/football-predictor](https://github.com/yukunai/football-predictor) | P2 | E1 | ClubElo与DC参考项目 |
| [Luis-ntonio/Match_Prediction](https://github.com/Luis-ntonio/Match_Prediction) | P2 | E1 | 国际队数据不适合大部分俱乐部竞彩 |
| [RKarnik10/world-cup-predictor](https://github.com/RKarnik10/world-cup-predictor) | P3 | E1 | 国际队项目，第三方数据有非商用条款 |
| [Divyadhole/world-cup-match-predictor](https://github.com/Divyadhole/world-cup-match-predictor) | P3 | E1 | 附小型合成数据不能用于真实结论 |
| [martj42/international_results](https://github.com/martj42/international_results) | P2 | E1 | 国际比赛历史结果候选 |
| [DOsinga/football_predictions](https://github.com/DOsinga/football_predictions) | P3 | E1 | 杯赛模拟可混合赔率，不是独立俱乐部模型 |

### 源码核验的实质发现
- soccerdata 的 soccerdata/clubelo.py 明确向 http://api.clubelo.com/<date> 获取CSV，具备历史球队评分与别名映射的实现；其源代码是 Apache-2.0，但上游源接口连通性仍单独验证。
- penaltyblog 的 penaltyblog/models/dixon_coles.py 确有独立拟合、低比分相关修正与概率网格的原版实现；MIT。我们尚未执行该第三方整套模型。可选择性在Windows隔离环境用有证据的赛前球队历史小批量试。
- dank0i 的 tests/test_leakage.py 真实包含修改未来20场比分不改变更早 Elo、修改本场结果不影响本场 form、和 as-of 时间截断等反事实防泄漏测试。README 自报16,888场留出：独立Log Loss 0.9817 vs 市场0.9728；未独立复现，不应复述成 EV-Lab 的成绩。该仓库根目录未找到 LICENSE：只借鉴思想，不复制源码。
- alexander-quang-phan 的 README 指出赛后排名伪装赛前字段的错误，以及平局类 argmax recall 接近0的警示。对 EV-Lab 的正负例审计比再堆一个XGBoost更直接。
- Hicruben 的 lib/model.ts 和 GitHub daily workflow 真实存在赛前快照、Git提交、鲜度检查以及 ClubElo→Dixon-Coles 路线，但 API-Football 需要凭据，Git提交能否证明每条预测在开赛前仍需逐场审核。作者自称的模型排名不作为证据。
- OPaheimer 的 weekly_loop.py 真有 freeze/grade/performance_ledger；但带 --force 参数可替换并归档旧快照，且 regrade 可覆盖当前评分。EV-Lab 自己的 sealed 证据制度不能照搬这个可覆盖行为。
- kaspersgit 的 src/model/features.py 和 train.py 显示市场赔率、overround、market bias 特征进入预测模型。可借鉴 autoresearch 研究账本，但**禁止将该实现作为独立预测层**，否则违反本项目 Odds/Model 隔离。

### 三个公开数据通道 E3 小型实测
1. **ClubElo 日期历史API：FAIL（当前Windows链路）**。https://api.clubelo.com/2026-10-10 与 /Liverpool TLS握手超时；http://api.clubelo.com/2026-10-10 返回502。只证明当前路径失败，不宣称API永久关闭。
2. **openfootball JSON：HTTP200但日期不符合**。下载 https://raw.githubusercontent.com/openfootball/football.json/master/2026-27/en.1.json：55,359字节，SHA256 bb91f0ab3e8359df163bb9ec98549bfed85e200dd4c32f3bd606b5890d932dd2，380场赛程仅45场有完整比赛比分，最后一场有比分记录日期是2026-09-20。不能补我们10月数据，不具有赛前快照保证。
3. **StatsBomb 比赛事件目录：HTTP200但覆盖不合**。https://raw.githubusercontent.com/statsbomb/open-data/master/data/competitions.json：34,887字节，SHA256 e6cd42f5d8956d6aa30fb917ce8d4c3b3df1879a93f02f8feba820930a6971fa；80赛事-赛季条目，名字没有2026赛季；非本169场的即时xG/阵容数据源。
4. 已有 FOOTBALL-DATA.CO.UK 正例：EV-Lab TASK0033 已实际取得6联赛×2赛季CSV、保存SHA并跑样本外比较，是当前确认E3可用的数据源之一；但对这169场28类赛事覆盖不足。不要把已下载的现代CSV误当当年每个字段的PIT版本。

### 论文与方法谱系
通过既有 A股项目验证过的 OpenAlex 方法再次直连查询，确认 Dixon & Coles (1997), DOI https://doi.org/10.1111/1467-9876.00065，以及 The value of statistical forecasts in the UK association football betting market (2004), DOI https://doi.org/10.1016/j.ijforecast.2003.12.007。当前只是来源元数据证实，不称已复现1997年盈利结论。

## 真正固化的能力而非仅登记
新增独立写出的 tests/test_discovery_temporal_adversarial.py，借鉴公开项目的反事实思想，对 EV-Lab 现有 task0032 独立概率模块实测：
1. 篡改未来日期的赛果，不应改动此前预测。
2. 篡改盘口概率，不应改动独立模型概率，只有市场评价会变动。
这两个测试不复制无许可证第三方代码，也不扩大主线模型或优化135场历史结果。

## 最终分级决策
**P0 已吸收**：反未来污染测试、冻结与QA审查流程、跨来源文献索引，直接用原来的 WebCodex/GitHub/OpenAlex，不另装搜索平台。
**P1 值得下一次受控实验**：penaltyblog 对照真正已有充分历史的 Dixon-Coles；soccerdata **单一**数据适配器的具体可用性；theopenmodel 逐场核对历史公开快照的开赛前Git证据。
**P2 仅备查**：openfootball、StatsBomb事件数据、足球国字号项目。不给本场相关覆盖时不纳入生产数据。
**P3 当前拒绝**：把赔率塞进自称“独立”的模型、合成数据假回测、无明确许可的大规模复制或再建昂贵爬虫堆栈。

**本支线到此有独立结论：** 开源研究资产确实可以让 EV-Lab 少走弯路。最有价值的是搜索后的 **时间有效性、身份桥、真实样本外对照及反向泄漏 QA**，其次才是更复杂模型。此轮没有发现已证明超过竞彩市场的可直接上线系统，也没有借此改写 EV-Lab 的此前 NO-EDGE 结论。
