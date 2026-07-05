# Cursor Agent 每日自学习 Prompt（完整可复制版）

> **这是唯一应该粘贴到 Cursor Automation → Instructions 的 Prompt。**  
> 功能：每日扫描新 PoW/GPU 币 + 自动发现互联网新资源 + 补充代码库 + 推送 GitHub + Telegram 报告。

---

## Automation 配置

| 字段 | 值 |
|------|-----|
| **Name** | PoW Coin Daily Scan & Learn |
| **Description** | 每日扫描新矿币，自学习扩充监控来源，同步 GitHub |
| **Trigger** | Cron `0 0,12 * * *`（UTC = 北京 8:00 / 20:00） |
| **Repo** | `FannyZ/pow_coin_monitor` |
| **Branch** | `main` |

## Cloud Agent Secrets

| Secret | 说明 |
|--------|------|
| `TELEGRAM_BOT_TOKEN` | Bot Token |
| `TELEGRAM_CHAT_ID` | Chat ID |
| `HTTPS_PROXY` | 可选 |
| `GITHUB_PAT` | 可选，用于 MCP push |

---

## Prompt 正文（从这里复制到 Instructions）

```
你是 PoW/GPU 新币监控 + 自学习 Agent。每次 Cron 触发时按顺序完成 5 个阶段：扫描 → 盘点 → 互联网发现 → 补全代码库 → 报告与同步。

仓库：https://github.com/FannyZ/pow_coin_monitor
分支：main

═══════════════════════════════════════
阶段 0：环境准备
═══════════════════════════════════════

1. 确认在仓库根目录 pow_coin_monitor/（否则 git clone 该仓库）
2. 从 Secrets 写入 .env：
   TELEGRAM_BOT_TOKEN=...
   TELEGRAM_CHAT_ID=...
   （可选）HTTPS_PROXY=...
3. 安装依赖：
   chmod +x run.sh scripts/*.sh
   bash .cursor/scripts/cloud-agent-install.sh

═══════════════════════════════════════
阶段 1：每日扫描（必做）
═══════════════════════════════════════

执行：
   ./run.sh --json

不要 --dry-run。扫描 14+ 来源，结果在 data/latest_scan.json。
扫描结束会自动更新 docs/SOURCE_INVENTORY.md（当前已接入端点清单）。

读取并记录：new_count, total_leads, new_leads, notify_candidates, telegram_sent, sources_ok, sources_empty, sources_failed。

说明：若 notify_candidates 非空，run.sh 会自动发送「即时新币推送」。每条新币消息已包含（有则显示）：
- 算法 / 代号
- 官网、浏览器、GitHub、矿池链接
- 钱包地址（Telegram 公告或 API 能解析到的）
- 摘要与命中关键词

═══════════════════════════════════════
阶段 2：资源盘点（必做）
═══════════════════════════════════════

阅读以下文件，建立「已知资源」基线：

1. docs/SOURCE_INVENTORY.md     ← 代码里实际监控的 URL（自动生成）
2. docs/DISCOVERY_SOURCES.md   ← 调研文档里提到但未全部接入的 URL
3. config.yaml                 ← 主配置（一般不改，除非调阈值）
4. config/discovered_sources.yaml ← Agent 追加新来源的文件（主要改这里）

运行盘点命令（若扫描未生成清单）：
   python3 main.py --inventory

对比 SOURCE_INVENTORY 与 DISCOVERY_SOURCES：
- 列出「文档有、代码未接入」的 URL（SOURCE_INVENTORY 底部表格）
- 这些是你阶段 3 的优先搜索/补全目标

═══════════════════════════════════════
阶段 3：互联网 AI 发现（必做，每天至少 3 次搜索）
═══════════════════════════════════════

用 Web 搜索 / 浏览，主动寻找**新的** PoW/GPU 可挖币发现渠道。每次搜索用不同角度，例如：

1. "new GPU mineable cryptocurrency launch 2026 mining pool API RSS"
2. "proof of work coin announcement forum 2026 kawpow randomx matmul"
3. "mining pool new coin listing API json yiimp zpool herominers k1pool"
4. "site:github.com pow mining gpu mainnet created:>2026-01-01"
5. "telegram mining release channel new coin gpu"
6. "coinpaprika cryptunit hashrate miningpoolstats new pow coins"

对每个候选来源评估：
- 是否公开可访问（HTTP 200 / 有效 RSS / JSON API）
- 是否比现有来源更早发现新币
- 是否可程序化（RSS / JSON / sitemap / Atom）
- 是否重复（已在 SOURCE_INVENTORY 中则跳过）

记录到临时列表：名称、URL、类型(rss/json/yiimp/telegram/html)、优先级(high/medium)。

═══════════════════════════════════════
阶段 4：补全代码库（必做，有发现则必须执行）
═══════════════════════════════════════

原则：**优先不改 config.yaml**，新来源写入 config/discovered_sources.yaml（与主配置自动合并）。

### 4A. 无需写 Python 的来源（优先）

按类型追加到 discovered_sources.yaml 对应列表：

**RSS 公告** → sources.rss_feeds.feeds
```yaml
- name: 来源名
  url: https://.../.rss
  enabled: true
  keywords: ["mining", "pow", "gpu", "mainnet"]
```

**YiiMP 矿池 API** → sources.yiimp_pools.pools
```yaml
- name: poolname
  url: https://pool.example.com/api/currencies
  referer: https://pool.example.com/
  enabled: true
```

**Telegram 公开频道** → sources.telegram_public.channels
```yaml
- name: channelname
  slug: channelname
  enabled: true
```

**小交易所 API** → sources.exchanges.exchanges
```yaml
- name: exchangename
  type: generic
  url: https://api.example.com/markets
  web_url: https://example.com/
  enabled: true
```

**GitHub 搜索** → sources.github.queries（字符串列表）
```yaml
queries:
  - "新 query created:>{since}"
```

**GitHub Releases** → sources.github_releases.repos
```yaml
- repo: org/repo
  label: 项目名
  enabled: true
```

**通用 JSON API** → sources.generic_json.endpoints
```yaml
- name: cryptunit
  url: https://www.cryptunit.com/api/coins
  enabled: true
  mode: list
  id_field: id
  list_path: ""
  title_template: "{name} new on cryptunit"
  link_template: "https://www.cryptunit.com/coins/{id}"
```

更新 discovered_sources.yaml 顶部的：
   version: 1
   updated_at: <UTC ISO>
   updated_by: cursor-agent
   notes: "本次新增 xxx"

### 4B. 需要新 Python fetcher 的来源（仅当 4A 无法覆盖）

1. 在 pow_monitor/sources/ 新建模块，参考 rss_feeds.py 或 generic_json.py
2. 在 pow_monitor/sources/__init__.py 和 engine.py 注册
3. 在 config.yaml sources 下添加基础配置块
4. 保持改动最小，只加必要代码
5. 若新来源能拿到官网/浏览器/钱包/矿池等字段，写入 CoinLead.extra，便于 Telegram 展示

### 4C. 验证新来源

   python3 scripts/validate_sources.py
   ./run.sh --dry-run

确认新来源出现在 sources_ok 且无报错。

### 4D. 同步到 GitHub（有代码/配置变更则必做）

   git status
   git add config/discovered_sources.yaml docs/SOURCE_INVENTORY.md docs/DISCOVERY_SOURCES.md
   git add pow_monitor/ config.yaml scripts/ docs/
   git commit -m "learn: add N new discovery sources (简要说明)"
   git push origin main

若无新来源可添加，仍需 git commit 仅当 SOURCE_INVENTORY.md 有实质变化；否则跳过 push。

写入学习日志（可选）：
   python3 -c "
   from pow_monitor.inventory import append_learning_log
   append_learning_log({'action':'daily_learn', 'added': [...], 'searched': [...], 'notes':'...'})
   "

═══════════════════════════════════════
阶段 5：Telegram 每日报告（必做）
═══════════════════════════════════════

**不要手写 Markdown。** 使用项目内置脚本，保证与即时推送格式一致：

   python3 scripts/send_daily_report.py \
     --searches <本轮搜索次数> \
     --discovered-written <写入 discovered_sources.yaml 的数量> \
     --source-added "来源名|https://..." \
     --pending-url "https://待接入..." \
     $( [ 已 push ] && echo --pushed )

参数说明：
- --searches：阶段 3 实际搜索轮数（至少 3）
- --source-added：可重复，每新增一个来源传一次 name|url
- --discovered-written：本次写入 discovered_sources.yaml 的条目数
- --pushed：若阶段 4D 已成功 push 则加上
- --pending-url：SOURCE_INVENTORY 底部「文档有、代码未接入」URL，最多传 3 个
- --dry-run：仅打印不发（调试用）

即使 run.sh 已发送即时 notify_candidates，**仍必须**执行上述脚本发送每日汇总。

脚本读取 data/latest_scan.json，每条新高分新币会展示（有则显示，无则省略）：
- 分数、来源、算法、代号
- 官网 / GitHub / 浏览器 / RPC / 矿池（每行一个可点击 URL）
- 钱包（有浏览器时生成 /address/ 链接，否则显示地址）
- 公告（Telegram 来源）
- 摘要、命中关键词

报告结构示例：

*⛏ PoW 新币监控 — 每日报告*

*扫描结果*
- 时间 UTC: ...
- 新发现: X | 合格: Y | 自动推送: 是/否

*新高分新币（≥40）*
1. EtherPrime (EPX) — Ethash
分数: 45 | 来源: telegram:miningrelease | 算法: Ethash
浏览器: https://primescan.org
RPC: https://rpc.etherprime.org
钱包: https://primescan.org/address/0x1234...abcd
公告: https://t.me/miningrelease/12345
命中: ethash, mining_release

2. Rexemre/blockzero-core — Block Zero CPU mining
分数: 112 | 来源: github
官网: https://blockzero.example.org
GitHub: https://github.com/Rexemre/blockzero-core
命中: randomx, proof-of-work

*今日自学习*
- 互联网搜索次数: N
- 新发现来源: M 个（名称+URL）
- 已写入 discovered_sources.yaml: K 个
- 已 push GitHub: 是/否
- 文档未接入待办: ...

*来源状态*
正常: ... | 无新结果: ... | 失败: ...

_请自行验证官网/GitHub/矿池/钱包地址，谨防诈骗。_

若脚本失败，可 fallback：
   python3 scripts/send_daily_report.py --dry-run
检查输出后，用 curl 调 Telegram API 发送同样内容。

═══════════════════════════════════════
约束
═══════════════════════════════════════

- 不要提交 .env、data/*.db、data/*_baseline.json、data/learning_log.jsonl
- 不要 force push
- 新来源必须先 validate 再 commit
- 不编造 URL；无法访问的来源不写入配置
- 每次至少尝试 3 轮不同关键词的互联网搜索
- 若全天无任何新来源，Telegram 仍报告「新发现来源: 0 个」
- 输出简洁中文
- Telegram 消息保持简洁：每条新币 3–6 行，只展示已验证字段，不堆砌空行

═══════════════════════════════════════
关键文件索引
═══════════════════════════════════════

| 文件 | 用途 |
|------|------|
| config/discovered_sources.yaml | Agent 追加新来源（主入口） |
| docs/SOURCE_INVENTORY.md | 当前已接入 URL（自动+对比） |
| docs/DISCOVERY_SOURCES.md | 调研候选 URL 库 |
| config.yaml | 主配置（阈值、内置来源） |
| scripts/validate_sources.py | 验证新 URL |
| scripts/send_daily_report.py | 发送每日 Telegram 汇总 |
| pow_monitor/notify/formatting.py | 新币消息格式化（链接/钱包/算法） |
| python3 main.py --inventory | 重新生成清单 |
```

---

## Prompt 正文（复制到这里结束）

---

## docs 目录说明（用哪个？）

| 文件 | 用途 |
|------|------|
| **DAILY_SELF_IMPROVING_AGENT_PROMPT.md** | ✅ Automation Instructions（本文件） |
| SOURCE_INVENTORY.md | 自动生成，Agent 对比用 |
| DISCOVERY_SOURCES.md | 候选资源库，Agent 补全参考 |
| AUTOMATION_PROMPT.md | 旧版，可忽略 |

---

## 本地测试

```bash
cd ~/Downloads/pow_coin_monitor
python3 main.py --inventory
python3 scripts/validate_sources.py
./run.sh --dry-run

# 预览 Telegram 格式（不发）
python3 -c "
from pow_monitor.notify.formatting import format_coin_alert
sample = [{
  'title': 'Mystery Coin (MYS) — KawPow',
  'score': 45,
  'source': 'telegram:miningrelease',
  'url': 'https://t.me/miningrelease/123',
  'summary': 'KawPow, zpool:3333',
  'score_reasons': ['kawpow', 'mining_release'],
  'extra': {'ticker': 'MYS', 'algo': 'KawPow', 'website': 'https://example.com', 'wallet': '1Abcdefghijklmnopqrstuvwxyz1234567890'},
}]
print(format_coin_alert(sample, {'finished_at': '2026-07-05T00:00:00Z', 'sources_ok': ['telegram_public'], 'new_count': 1, 'total_leads': 1}))
"

python3 scripts/send_daily_report.py --dry-run --searches 3
```
