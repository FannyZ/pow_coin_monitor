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
