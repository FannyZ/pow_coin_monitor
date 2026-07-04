# Cursor Automation — PoW 新币每日扫描 + Telegram 推送

复制下面整段 **Instructions / Prompt** 到 Cursor Automations 编辑器。  
Telegram 凭证从 `btc_trend_monitor` 项目复用（或你在 Automation Secrets 里单独配置）。

---

## 推荐 Automation 配置

| 字段 | 值 |
|------|-----|
| **Name** | PoW Coin Daily Scan |
| **Description** | 每日扫描互联网新 PoW/GPU 可挖币，Telegram 推送结果 |
| **Trigger** | Cron：`0 0,12 * * *`（UTC 0:00 / 12:00 = 北京 8:00 / 20:00） |
| **Repo** | `FannyZ/pow_coin_monitor` |
| **Branch** | `main` |
| **Tools** | Shell / Terminal（允许运行脚本） |

---

## Instructions（Agent Prompt — 直接粘贴）

```
你是 PoW/GPU 新币监控自动化 Agent。每次触发时完成以下任务，并把结果发到 Telegram。

## 仓库
- 工作目录：当前 checkout 的 `pow_coin_monitor` 仓库根目录
- 若不在仓库内，先 `git clone https://github.com/FannyZ/pow_coin_monitor.git` 并 cd 进入

## Telegram 凭证（二选一，优先 A）
A. 从 btc_trend_monitor 同步（本地/同机 Cloud Agent）：
   - 读取 `~/Downloads/btc/btc_trend_monitor/.env` 中的 `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID`
   - 写入本仓库 `.env`（若不存在则从 `.env.example` 复制）
B. 使用 Automation Secrets / 环境变量：
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

## 可选代理（国内网络）
若 BitcoinTalk / 矿池 API 超时，在 `.env` 添加：
`HTTPS_PROXY=http://127.0.0.1:7890`

## 执行扫描
```bash
chmod +x run.sh scripts/*.sh
./run.sh --json
```
不要加 `--dry-run`。正式扫描，有新高分币应推送 Telegram。

## 读取结果
扫描完成后读取 `data/latest_scan.json`，提取：
- `finished_at`
- `new_count`
- `total_leads`
- `sources_ok` / `sources_failed` / `sources_empty`
- `new_leads`（全部列出）
- `notify_candidates`（分数 ≥ notify_min_score 的项）
- `telegram_sent` 是否为 true

## Telegram 二次摘要（必做）
即使 `./run.sh` 已推送，再发一条汇总消息（Markdown），格式：

*⛏ PoW 新币监控 — 每日报告*
扫描时间 UTC: {finished_at}
新发现: {new_count} | 合格线索: {total_leads}
Telegram 自动推送: {是/否}

*新高分新币（若有）*
1. [分数] 标题 — 来源 — URL
...

*来源状态*
- 正常: ...
- 无新结果: ...
- 失败: ...

若无新币，也要发送简短报告："本次扫描无新发现，各来源基线正常。"

## 失败处理
- 若 venv 缺失：运行 `./scripts/ensure_venv.sh` 后重试
- 若 Telegram 未配置：在报告中说明缺少 TELEGRAM_*，扫描结果仍写入 `data/latest_scan.json`
- 若单源超时：记录日志，不中断整体任务
- 退出码非 0 时在 Telegram 说明失败原因

## 约束
- 不要修改源代码，除非依赖安装失败
- 不要提交 `.env` 或 `data/*.db`
- 输出简洁中文，链接保留完整 URL
```

---

## 本地手动测试（Automation 上线前）

```bash
cd ~/Downloads/pow_coin_monitor
grep '^TELEGRAM_' ~/Downloads/btc/btc_trend_monitor/.env >> .env   # 或手动填写
./run.sh
python3 scripts/test_telegram.py
```

---

## Secrets 清单（Cloud Agent 推荐）

在 Cursor Dashboard → Automation Secrets 配置：

| Secret | 说明 |
|--------|------|
| `TELEGRAM_BOT_TOKEN` | 与 btc_trend_monitor 相同 |
| `TELEGRAM_CHAT_ID` | 与 btc_trend_monitor 相同 |
| `HTTPS_PROXY` | 可选，国内运行时需要 |

然后在 Prompt 里把「凭证 A」改为「使用环境变量 Secrets」。
