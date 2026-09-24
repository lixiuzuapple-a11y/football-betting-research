# Scrapling 侦察：`D4Vinci/Scrapling` 可否借鉴或采用

- 日期：2026-09-24
- 项目：football-betting-research
- 类型：External Reconnaissance / Tool Evaluation + Scope-Change Request
- 版本：v1
- 状态：Submitted for Reviewer decision — **未采纳、未安装、未改动任何代码或研究结论**
- 提交人：WorkBuddy / Executor（应 Owner 直接指令发起；非 TASK 派生）
- 说明：本文件由 Owner 指令发起，不属 TASK-0004 范围，也不占用 TASK 编号。
  Executor 仅作事实采集与整理；第 6、7 节的**提案性质内容为 Owner 立场**，已在各节内标注。

---

## 0. 结论摘要（先行）

1. **`Scrapling` 的反检测能力与本项目现行边界正面冲突**，且冲突项不是我方的推测，
   而是 TASK-0004 §G 与 "Stop and report before" 清单里逐条写明的禁止项。
2. **但即使放宽该边界，也解决不了我们当前真正的卡点。** D01-B 卡在
   「参考侧不暴露 provider 时间戳」——这是**数据源质量**问题，不是技术封锁问题，
   任何反检测/浏览器渲染工具都不能凭空造出上游没有的时间戳。
3. **能靠反检测获得增量收益的场景，几乎必然需要付费代理或付费绕过 API。**
   Owner 已给出约束：**"如果只能付费使用，那就算了。"** 该约束先行排除这类场景。
4. **可零成本、零合规风险借鉴的只有解析层**，且本机已有 `lxml`，**不必为此安装 Scrapling**。
   该借鉴价值已在本机独立复现（§4）。
5. 本轮另发现 **500.com 页面两个数据完整性缺陷**（§5），属独立于 Scrapling 的真实发现，
   与 TASK-0004 的数据质量相关，建议 Reviewer 决定是否需要 erratum。
6. **Executor 建议：不采用、不安装。** 理由与替代方案见 §8。

---

## 1. 证据等级声明

沿用 `research/literature/GITHUB_OPEN_SOURCE_SCOUT_20260922_v3_0.md` 的分级制度。

| 对象 | 本轮等级 | 依据 | 未做什么 |
|---|---|---|---|
| `D4Vinci/Scrapling` 本体 | **SCOUTED** | 已读 README、官方文档站 StealthyFetcher 页、GitHub API 元数据 | **未读源码**；未 clone；未安装；未运行其任何代码 |
| 「声明式解析可无损替代手写正则」这一方法 | **REPRODUCED**（在本机、用我们自己的数据） | §4 等价性实测，9/9 | 复现的是**方法**，不是 Scrapling 的实现 |
| 500.com 页面两个缺陷 | **REPRODUCED** | 字节级复现 + 可重跑命令 | — |

> **明确不作数的证据**：本仓库既有规则写明「项目知名度、Star 数、README 中的收益结果，
> 均不提高证据等级」。因此下表的 Star 数等元数据**只用于淘汰"死项目"**，
> **不构成任何采纳理由**。

**因此：本文件不支持任何"直接应用 Scrapling"的结论。** 它的等级上限是 SCOUTED。
若 Reviewer 认为值得推进，需要先补一次源码级审计（PARTIAL AUDIT 起）。

---

## 2. 项目事实（SCOUTED 级）

| 项 | 值 |
|---|---|
| 仓库 | `https://github.com/D4Vinci/Scrapling` |
| 作者 | Karim Shoair（D4Vinci） |
| 许可证 | **BSD-3-Clause**（宽松；依赖含改编自 Parsel 的 BSD 代码） |
| Python 要求 | **≥ 3.10**（本机 3.13.14 ✓） |
| 最新发布 | **v0.4.15（2026-08-23）** |
| 最近提交 | 2026-09-23 |
| 元数据 | 83,205 star / 8,494 fork / 3 open issue（**仅用于判断项目存活，不提高证据等级**） |
| 成熟度风险 | **仍是 0.4.x 预 1.0**。v0.3.13 将底层引擎由 Camoufox 换为 **patchright**，属破坏性变更 → 若采用必须钉死版本 |

### 组件与能力

| 组件 | 能力 | 官方文档原文要点 |
|---|---|---|
| `Selector` / 解析器 | CSS / XPath / 文本 / 正则选择，自适应元素追踪 | 与抓取解耦，可独立使用（`Selector("<html>…")`） |
| `Fetcher` | HTTP 请求，可**伪装浏览器 TLS 指纹**，支持 HTTP/3 | "Can impersonate browsers' TLS fingerprint" |
| `DynamicFetcher` | Playwright Chromium 全浏览器渲染 | — |
| `StealthyFetcher` | 指纹伪装 + **主动解 Cloudflare 挑战** | "It easily bypasses all types of Cloudflare's Turnstile/Interstitial automatically"；含 `solve_cloudflare`、`hide_canvas`（画布加噪）、`block_webrtc` |
| `Spider` | 并发、暂停/恢复、AutoThrottle、**`ProxyRotator` 代理轮换** | — |

### 必须同时记录的动机事实

- README 赞助商为**代理服务商**（DataImpulse）与**企业级反爬绕过 API 供应商**
  （Hyper Solutions，宣称覆盖 Akamai / DataDome / Kasada / Incapsula）。
- 换言之：**免费默认能力在硬防护站点会撞墙，文档顺手指向付费赞助商。**
  若指望用它解决硬防护，路径终点是**买代理或买绕过 API**。
- 项目自带免责声明：**仅供教育与研究用途**，使用方须自行遵守当地法律与 robots.txt。

---

## 3. 与现行边界的逐条冲突（本文件核心）

### 3.1 边界原文（逐字引用 `TASKS/TASK-0004-synchronized-dual-market-capture.md`）

访问方式升级顺序（§G）：

> `existing collector / requests -> inspect HTML/JS/XHR when needed -> bounded browser rendering only if genuinely required`

同一节禁止项：

> - do not bypass WAF/access controls;
> - do not rotate IPs/proxies/VPNs;
> - do not reuse the historical IP-rotation workaround as current authorization;
> - do not deploy Cloudflare Workers in TASK-0004 without separate Reviewer authorization.

> The historical mention of IP rotation is evidence about an old environment, **not permission to reproduce it**.

"Stop and report before" 清单（需先停下并上报的动作）：

> - creating an account;
> - buying a data/API plan;
> - using new credentials;
> - **bypassing access controls**;
> - **changing proxy/VPN/system configuration**;
> - installing a system service.

### 3.2 能力 ↔ 红线映射

| Scrapling 能力 | 命中的边界条款 | 判定 |
|---|---|---|
| `StealthyFetcher(solve_cloudflare=True)` | "do not bypass WAF/access controls" | **明确冲突** |
| `ProxyRotator` / 任何代理轮换 | "do not rotate IPs/proxies/VPNs" | **明确冲突** |
| `Fetcher(impersonate='chrome')` TLS 指纹伪装 | "do not bypass WAF/access controls"（目的即让反爬认不出脚本） | **冲突** |
| `hide_canvas` / `block_webrtc` | 同上（对抗指纹识别与检测） | **冲突** |
| `Fetcher` 普通 HTTP 请求 | 无 | 不冲突 |
| `Selector` 解析 | 无（纯本地、无网络、无检测对抗） | **不冲突** |
| `capture_xhr` | 对应已授权的 "inspect HTML/JS/XHR" 一步 | **不冲突**（但若为此引入浏览器渲染，回到升级顺序的第 3 级，需"确实必要"） |
| `AutoThrottle` 自动退避 | 无（遇阻加倍延迟，方向与规避相反） | 不冲突 |
| `Spider` 并发/暂停恢复 | 无 | 不冲突（但含 `ProxyRotator` 的组合用法冲突） |
| Docker 镜像 | 无 | 不冲突 |

### 3.3 一个加重情节

TASK-0004 上一轮报告中，Executor **连"补一个 `Referer` 头是否越线"都不敢自行判定**，
已专门留作 Reviewer 裁决点。

`Scrapling` 的 `solve_cloudflare` / 代理轮换是**目的性规避工具**，
比补一个 header 的量级重得多。若以其替换一个**正在被审查**的动作，
等于用更重的越线动作覆盖较轻的争议动作——这是 Executor 明确不拟自行推进的第一个理由。

### 3.4 本项目已有的同类立场（先例）

`GITHUB_OPEN_SOURCE_SCOUT_20260922_v3_0.md` 中，同类工具已被 Reviewer 判为：

> `jordantete/OddsHarvester`（OddsPortal scraper）— 风险：**ToS、反爬、页面变化；不宜做核心生产源** — 优先级 **P2**

即：**反爬/规避类工具在本项目既有口径中已是 P2，且"不宜做核心生产源"。**
本轮结论与该先例一致。

---

## 4. 实测：可借鉴部分（REPRODUCED）

### 4.1 方法

不联网、不安装任何新依赖，用**本机已抓取的 500.com 快照**，
将「手写正则解析」与「声明式 XPath 解析」（Scrapling 的用法形态）对拍。

- 快照：`r3_mirror_500_today_091344.html`，114,505 字节
- sha256：`5a897a517e8dc0a3711f49c901c7f3faa9da145928ee02852be3068b80d697e6`
- 对照基准：`phasec_round3.json` 中 `sources.mirror_500_today.rows`（由现行正则解析器产出）
- 脚本：本地 `probe2/sp1_selector_equiv.py`（未入库；如需可随 erratum 一并提交）

### 4.2 结果

```
regex rows       = 9
declarative rows = 9
declarative-vs-regex : matched=9  mismatched=0
```

**9/9 逐值一致**：场次号、开赛日期、开赛时间、标准 1X2（`nspf`）、让球 1X2（`spf`）全部相等。

### 4.3 本机环境

`lxml 6.1.1`、`curl_cffi 0.16.2` **已存在**；`scrapling` 未安装。

> 注：`curl_cffi` 正是 Scrapling `Fetcher` 做 TLS 指纹伪装所用的底层。
> **能力已在机器上，是否使用是授权问题，不是安装问题**——这一点请 Reviewer 注意。

### 4.4 该结论的边界

- 证明的是：**换用声明式解析在我们这个页面上是无损替换**，不是重写风险。
- **没有**证明：Scrapling 的实现更优、更快、更稳。未做源码审计，不做该主张。
- 等价性只在**单一快照、单一页面**上验证。多站点/多版本泛化未测。

---

## 5. 新证据：500.com 页面的两个数据完整性缺陷（REPRODUCED）

> Owner 明确要求作为**新证据**上报。以下两条**与 Scrapling 无关**，
> 是我们自己采集链路的发现，与 TASK-0004 的数据质量有关。

### 5.1 缺陷一：页面为混杂编码，**没有单一 codec 能整体解码**

- 页面声明 `<meta charset="gb2312">`，正文绝大多数为 GBK；
- 但第 **77,510** 字节处嵌入一段 **UTF-8** 的 JS 对象字面量：

  ```html
  <input type="hidden" id="jsonggtype" value="{'单关':58,'2串1':1,'3串1':3,…}">
  ```

  （内容为过关方式表；`单关` 的字节为 `\xe5\x8d\x95\xe5\x85\xb3` = UTF-8）

- 实测各 codec 的解码失败位置：

  | codec | 结果 |
  |---|---|
  | `utf-8` | **FAIL** @ byte 61（GBK 的"竞彩足球"） |
  | `gbk` | **FAIL** @ byte 77,510（上述 UTF-8 片段） |
  | `gb18030` | **FAIL** @ byte 77,510 |
  | `gb2312` | **FAIL** @ byte 77,495 |
  | `latin-1` | 可解码，但语义无意义 |

  → **没有任何单一 codec 能解全该文档。**

- **危险点**：若按 `utf-8` + `errors='ignore'` 读取，**中文会被静默丢弃且不抛异常**：
  - `data-matchnum="周三003"` → 变成 `"003"`
  - 队名全部变成乱码（如"西雅图"→ `ͼ`）

- **当前影响评估：潜在，非已发生。** 现行解析器只读取 GBK 区域，未解析 `jsonggtype`，
  故 **TASK-0004 已提交的 9 行结果未受影响**（已用正确解码复算，9/9 一致）。
  但「该页面必须分段/显式解码」是一条**此前未记录的硬规则**，
  任何后续解析该字段的实现都会中招。

### 5.2 缺陷二：`data-matchnum` 的后三位**不唯一**

- `周三003` 与 `周四003` 的后三位均为 `003`。
- 若以「后三位」作为比赛键，两场会**静默碰撞**。
  （本轮验证脚本首次运行即因此误报 1 例假 DIFF，修正为完整匹配后归零。）
- 相关事实：`周三003` 那一行为 `class="bet-tb-tr bet-tb-end"` + `style="display:none"`
  （**已结束的隐藏行**）。页面上共 9 行，**实际在售仅 8 行**。
- 即：**该页存在"隐藏的已结束行 + 复用的场次序号"两个叠加陷阱**，
  任何按序号 join 的逻辑都需要显式排除 `bet-tb-end`。

### 5.3 可重跑命令（可复现性）

以下两条命令**已在本机实跑验证**，输出与上文一致。
`P` 为 `r3_mirror_500_today_091344.html` 的路径。

**A) 各 codec 的失败位置：**

```python
b = open(P, "rb").read()
for enc in ("utf-8", "gbk", "gb2312"):
    try:
        b.decode(enc); print(f"  {enc:8} OK")
    except UnicodeDecodeError as e:
        print(f"  {enc:8} FAIL at byte {e.start} bytes={b[e.start:e.start+6]!r}")
```

实测输出：

```
  utf-8    FAIL at byte 61 bytes=b'\xa1\xbe\xbe\xba\xb2\xca'
  gbk      FAIL at byte 77510 bytes=b"\xb21':1,"
  gb2312   FAIL at byte 77495 bytes=b'\xe5\x8d\x95\xe5\x85\xb3'
```

**B) `utf-8 + errors='ignore'` 的静默丢字：**

```python
import re
for enc in ("utf-8", "gbk"):
    t = b.decode(enc, errors="ignore")
    print(enc, re.search(r'data-matchnum="([^"]*)"', t).group(1))
```

实测输出：

```
utf-8 003
gbk 周三003
```

→ 同一段字节，`utf-8` 静默给出 `'003'`，`gbk` 给出 `'周三003'`。**前者不抛任何异常。**

### 5.4 请 Reviewer 裁决

1. 是否将 §5.1 / §5.2 作为 **erratum** 追加到已提交的 `REPORTS/TASK-0004.md`？
   （该报告当前处于 REVIEW。Executor **未自行修改**已提交报告。）
2. 是否要求在 `docs/data-policy.md` 或 provider 规范中，
   把「页面声明编码 ≠ 实际编码，必须显式解码并校验」写成硬约束？

---

## 6. 权限需求矩阵

> Owner 要求明确：**若使用 Scrapling，需要给 Executor 什么权限。**
> 本节为事实陈述，不含 Executor 主张。

### 6.1 按组件分档

| 档位 | 组件/动作 | 需要的授权 | 是否有成本 |
|---|---|---|---|
| **A. 现行已授权** | `Selector` 解析（纯本地）；`AutoThrottle` 思路；`capture_xhr` 思路 | 无（属 TASK-0004 已授权的 "inspect HTML/JS/XHR"） | 零 |
| **B. 需安装授权** | `pip install scrapling`（解析器） | 本机装依赖（需授权） | 零 |
| **C. 需安装授权 + 重资源** | `pip install "scrapling[fetchers]"` + `scrapling install` | 同上，且会下载**浏览器及系统依赖**；`patchright`/Playwright 栈 | 零，但机器负担重 |
| **D. 需放宽红线** | `Fetcher(impersonate=…)` TLS 指纹伪装 | 需 Reviewer/Owner 明确授权放开 "do not bypass WAF/access controls" | 零 |
| **E. 需放宽红线** | `StealthyFetcher(solve_cloudflare=True)` | 同上（明确解挑战） | 零 |
| **F. 需放宽红线 + 付费** | `ProxyRotator` 实际使用 | 同上放开 "do not rotate IPs/proxies/VPNs"，**且需真实代理** | **付费** |
| **G. 需放宽红线 + 付费** | 企业级绕过（Akamai/DataDome/Kasada） | 同上 | **付费（赞助商 API）** |

### 6.2 Owner 已给出的约束（binding）

> **"如果只能付费使用，那就算了。"** — Owner，2026-09-24

该约束**先行排除** F、G 两档。因 §7.2 的决策树显示增量收益集中在 F/G，
该约束实质上大幅压缩了本提案的空间。

### 6.3 另需注意

- `scrapling` 为 **0.4.x 预 1.0**，采用即须**钉死版本 + 建立回归测试**，
  否则上游破坏性变更（如 0.3.13 换引擎）会直接冲击我们的采集链。
- 本项目既有规则要求第三方库：锁版本、建 golden tests、不把库输出当真理。
  若走 C 档，上述成本须计入。

---

## 7. 红线变更提案（**Owner 提出**，Executor 附分析）

> **归属声明**：本节由 **Owner 老李** 决定正式提交 Reviewer 裁决。
> **Executor 不代表自己主张放宽红线**，仅代为整理陈述，并附上必要的可行性分析，
> 以便 Reviewer 在知情前提下裁决。

### 7.1 Owner 的提案

> 请 Reviewer 正式评估：是否允许为获取数据源而**放宽 "do not bypass WAF/access controls"
> 与 "do not rotate IPs/proxies/VPNs" 两条边界**。

### 7.2 Executor 附分析：按场景拆解（供裁决参考）

| 场景 | 是否免费 | 对我们卡点的实际收益 | 触及红线 |
|---|---|---|---|
| A. 本机 IP + 指纹伪装，访问原本就能访问的页面 | 免费 | **≈0**（能访问的本来就能访问） | 是 |
| B. 本机 IP + 解 Cloudflare 挑战 | 免费 | 中；但我方现行数据源均**不**受 Cloudflare 保护 | 是 |
| C. 轮换代理绕过 IP 限流（如 BetExplorer 429） | **需付费代理** | 中高 | 是 |
| D. 企业级绕过 Akamai/DataDome/Kasada | **需付费 API** | 高；但我方无此类目标源 | 是 |

**关键判断：能解决真实卡点的场景（C/D）必然付费 → 已被 Owner 的 §6.2 约束排除。
免费可行的场景（A/B）收益接近于零。**

### 7.3 Executor 附分析：反检测**不是**我们当前的瓶颈

这是本轮最重要的判断，请 Reviewer 重点核验：

- TASK-0004 现行结论为 `SMOKE CAPTURED / D01 TIMING PRECISION STILL UNRESOLVED`。
- **D01-B 的卡点是：BetExplorer 作为 `reference_proxy` 不暴露任何 provider 更新时间戳。**
  我们的告警原文即："参考侧无 provider 时间戳"。
- 这是**数据源质量/信息披露**问题，**不是**访问被封锁问题。
- **任何反检测、指纹伪装、浏览器渲染工具，都无法凭空生成上游从未提供的时间戳。**
  伪造/插值时间戳是本项目明令禁止项。
- 同理，官方 Sporttery 端点已由 `Referer` 头解决（非反检测手段），
  且官方端本身**提供** `updateDate/updateTime`。

→ **放宽红线不会让 D01-B 前进一步。** 它提高的是"能访问多少站点"，
而我们缺的是"已能访问的站点愿不愿意告诉我们时间"。

### 7.4 Executor 结论（供参考，非主张）

**建议不予放宽。** 理由：净收益接近零（§7.2），且不触及真实瓶颈（§7.3）；
同时会推翻本仓库对同类工具既有的 P2 口径（§3.4），并可能影响既有
`Referer` 争议的裁决基调（§3.3）。

---

## 8. 建议

1. **不采用 Scrapling。** 证据等级 SCOUTED，收益集中在被排除的付费档，
   且不解决真实瓶颈。
2. **不安装**（含 `pip install scrapling` 的轻量档）。解析层借鉴**不需要它**——
   本机已有 `lxml`，§4 已证明用 `lxml` 即可达成同等效果。
3. **可吸收其设计思路（零依赖）**：
   - 声明式选择器替代手写正则（§4 已验证无损）；
   - `AutoThrottle` 式退避（应对 BetExplorer 429 的**合规**手段：加大间隔，而非换 IP）；
   - 采集与解析解耦（与本仓库既有 `provider -> raw snapshot -> normalization` 方向一致）。
4. **§5 两个缺陷按 §5.4 提交 Reviewer 裁决。**
5. **若未来确有需要**，正确的顺序是：先补**源码级审计**（PARTIAL AUDIT 起），
   再谈组件级采用，且逐组件过边界，不做整体引入。

---

## 9. 需 Reviewer 裁决的问题

| # | 问题 | 性质 |
|---|---|---|
| Q1 | 是否采纳 §8 的建议（不采用/不安装，仅吸收设计思路）？ | 采纳决策 |
| Q2 | §5 的两个缺陷是否作为 erratum 追加至 `REPORTS/TASK-0004.md`？（Executor 未自行改动已提交报告） | 流程/数据质量 |
| Q3 | 是否要求把"页面声明编码 ≠ 实际编码"写入数据政策（`docs/data-policy.md`）？ | 规范 |
| Q4 | Executor 对 "500.com 页面必须显式解码" 的理解是否正确？请独立核验 §5.1。 | 技术核验 |
| Q5 | §7 红线提案：**是否放宽**？Executor 分析（§7.3）主张**不予放宽**，请独立核验该判断是否成立。 | 边界变更 |
| Q6 | 是否需要将 Scrapling 登入 `GITHUB_OPEN_SOURCE_SCOUT`，等级 **SCOUTED / REJECT**？ | 名录维护 |

---

## 附录：本轮 Executor 未做的事（边界自证）

- 未修改 `src/`、`tests/`、任何研究结论或 Edge Exhaustion Matrix；
- 未修改已提交的 `REPORTS/TASK-0004.md`；
- 未写入 `REVIEWS/`；
- 未安装 `scrapling` 或任何新依赖；
- 未进行任何绕过 WAF/访问控制的请求，未使用代理/VPN，未轮换 IP；
- 未触碰 TASK-0005 或任何相邻任务；
- 未改动 Git remote/config，未 force-push。
