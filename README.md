# PoW / GPU 新币监控 v2

从 **15+ 公开渠道** 扫描可直接参与挖矿（GPU/PoW）的新项目。配置方式与 `btc_trend_monitor` 相同。

> 完整渠道调研见 [docs/DISCOVERY_SOURCES.md](docs/DISCOVERY_SOURCES.md)（4 个 AI 模型集思广益结果）

## 监控来源（按优先级）

| 层级 | 来源 |
|------|------|
| **最早信号** | Telegram @miningrelease、YiiMP 矿池 API（Zpool/Zergpool/Rplant）、Reddit RSS |
| **矿池/社区** | RainbowMiner DB、2Miners Blog、MiningPoolStats sitemap、WhatToMine |
| **代码/发布** | GitHub Search + Releases Atom（BTX/Parallax 等） |
| **聚合/交易所** | CoinPaprika、XeggeX、NiceHash、SafeTrade、CoinGecko |
| **论坛** | BitcoinTalk ANN、LitecoinTalk RSS、HN RSS |

## 快速开始

```bash
cd ~/Downloads/pow_coin_monitor
cp .env.example .env   # TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID
chmod +x run.sh scripts/*.sh
./run.sh --dry-run
./run.sh
```

国内若部分源超时，在 `.env` 加：

```env
HTTPS_PROXY=http://127.0.0.1:7890
```

## Telegram

与 `Downloads/btc/btc_trend_monitor` 相同，测试：

```bash
source .venv/bin/activate
python3 scripts/test_telegram.py
```

## 命令

```bash
./run.sh --dry-run
./run.sh --no-telegram
./run.sh --json
```

## 输出

- `data/coins.db` — 去重数据库
- `data/latest_scan.json` — 最近扫描
- `data/*_baseline.json` — 各来源基线（防首次运行刷屏）

## 定时

```bash
0 8,20 * * * cd /Users/fan/Downloads/pow_coin_monitor && ./run.sh >> data/cron.log 2>&1
```

## Cursor Cloud Agent（已从 fitness 项目复制 GitHub 配置）

与 `~/Downloads/fitness/.cursor/` 相同模式：

| 文件 | 作用 |
|------|------|
| `.cursor/environment.json` | Cloud Agent 拉取 `FannyZ/pow_coin_monitor` |
| `.cursor/mcp.json` | GitHub MCP（`GITHUB_PAT`） |
| `.cursor/Dockerfile` | Cloud 运行环境 |
| `.cursor/scripts/cloud-agent-install.sh` | 安装 Python 依赖 |

```bash
# 1. 复制 GitHub PAT（与 fitness 共用，不提交 git）
cp ~/Downloads/fitness/.cursor/mcp.secrets.env ~/Downloads/pow_coin_monitor/.cursor/

# 2. 安装依赖 + 同步 Telegram
bash .cursor/scripts/setup-ai-dev.sh
source .cursor/mcp.secrets.env
```

Automation 说明见 `docs/AUTOMATION_PROMPT.md`。

## 推送到 GitHub

远程仓库需先在 GitHub 网页创建（fitness 的 `GITHUB_PAT` 无建库权限，只能读/PR）：

1. https://github.com/new → 名称 `pow_coin_monitor`，不要勾选 README  
2. `git push -u origin main`

或使用带 **repo** 权限的新 PAT：`./scripts/publish_github.sh`
