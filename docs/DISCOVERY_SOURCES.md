# 新 PoW/GPU 币发现渠道调研（多模型集思广益）

本文档汇总了 **GPT-5.3 Codex、GPT-5.5、Claude Sonnet 5、Composer 2.5** 四个模型对「从哪里最早发现可挖矿新币」的调研结果，并已将有 API/RSS/可抓取的部分接入 `pow_coin_monitor`。

## 已接入代码（可直接跑）

| 优先级 | 来源 | 类型 | 说明 |
|--------|------|------|------|
| ⭐⭐⭐ | **Telegram @miningrelease** | 公开频道 HTML | GPU 新币发布极早，常早于聚合器 |
| ⭐⭐⭐ | **Zpool / Zergpool / Rplant** | YiiMP JSON API | 矿池 `/api/currencies` 新 ticker |
| ⭐⭐⭐ | **Reddit RSS** | Atom/RSS | r/gpumining、r/cryptomining、关键词搜索 |
| ⭐⭐⭐ | **RainbowMiner coinsdb.json** | GitHub Raw JSON | 维护者已跟踪多矿池新币 |
| ⭐⭐ | **2Miners Blog RSS** | WordPress RSS | 新矿池公告 |
| ⭐⭐ | **GitHub Releases Atom** | Atom | BTX、Parallax、BlockZero 等 |
| ⭐⭐ | **MiningPoolStats sitemap** | XML | 新矿池页出现 |
| ⭐⭐ | **WhatToMine coins.json** | JSON | GPU 算法新币 |
| ⭐⭐ | **CoinPaprika is_new** | JSON API | 5 天内新收录 |
| ⭐⭐ | **XeggeX markets API** | JSON | 小所新上币 |
| ⭐ | **NiceHash algorithms** | JSON API | 新算法 = 潜在新币 |
| ⭐ | **HN RSS (hnrss.org)** | RSS | 开发者讨论 |
| ⭐ | **LitecoinTalk ANN** | Discourse RSS | 项目公告 |
| ⭐ | **GitHub Search** | REST API | 多 query 扩展 |
| ⭐ | **BitcoinTalk board 159** | HTML | 经典 ANN 板 |
| ⭐ | **SafeTrade / CoinGecko** | HTML/API | 交易所/聚合器 |

## 调研发现但未接入（需 API Key / 反爬 / 不稳定）

| 来源 | 原因 |
|------|------|
| CoinMarketCap listings/new | 需 Pro API Key |
| CoinGecko coins/list/new | 需 Pro API Key |
| Minerstat / Hashrate.no | 需付费 API Key |
| MiningPoolStats `/newcoins` | JS 渲染 + data API 403 |
| TradeOgre | Cloudflare 403 |
| BitcoinTalk RSS | 官方已关闭 board RSS |
| Bluesky / Nostr / Farcaster | 需额外 SDK 或 API Key |
| Discord 目录 | Discord 本身被墙，目录页不稳定 |

## 各模型独特贡献

### GPT-5.3 Codex — 广度清单
- AltcoinsTalks、Bitcoin Garden、Ergo Forum
- Zergpool/Rplant API、StakeCube、Exbitron、NonKYC news
- Mastodon hashtag RSS、DISBOARD 挖矿 Discord 目录

### Claude Sonnet 5 — 社区/矿池角度
- **miningpoolstats.stream/newcoins**（JS 页，难抓）
- HeroMiners / LuckyPool / K1Pool / Kryptex 首页 diff
- Reddit OAuth 长期方案（RSS 可能关闭）
- BitcoinTalk board 160/199（Mining/Pools）

### GPT-5.5 — 交易所 + 技术 API
- FreiExchange ticker API（30 req/min）
- Chainz/CryptoID explorer summary diff
- Blockchair supported chains
- Zpool `/api/status` 算法级监控

### Composer 2.5 — GitHub/RSS 深度
- CryptUnit `/api/coins` 新 id
- CryptoCompare coinlist PoW diff
- GitHub 高级 query（fair launch RandomX、org watchlist）
- CoinToMine、PoolBay 等 scrape 源

## 国内网络说明

部分源在国内可能超时，建议在 `.env` 配置：

```env
HTTPS_PROXY=http://127.0.0.1:7890
```

通常需要代理的：BitcoinTalk、SafeTrade、Zpool/Zergpool、NiceHash、CoinGecko。

通常可直连的：Telegram 公开页、Reddit RSS、MiningPoolStats sitemap、WhatToMine、GitHub、CoinPaprika（不稳定）。

## 每日推荐工作流

```bash
cd ~/Downloads/pow_coin_monitor
./run.sh --dry-run    # 先看有没有新币
./run.sh              # 有新高分新币则 Telegram 推送
```

首次运行各「基线型」来源（矿池 API、MPS、WTM 等）会建立基线，**不会误报历史币种**；从第二次开始只报新增。

## 后续可扩展（欢迎提需求）

1. HeroMiners / K1Pool / LuckyPool 首页 scrape
2. CryptUnit + CryptoCompare PoW diff
3. BitcoinTalk board 160/199 额外板
4. AltcoinsTalks / Bitcoin Garden 论坛
5. CMC/CoinGecko Pro（用户提供 API Key 后接入）
