# 当前监控资源清单（自动生成）

生成时间 UTC: 2026-07-08T01:04:45Z

- 活跃来源模块: **15**
- 活跃端点: **50**
- 文档中未接入 URL（待评估）: **0**

## 活跃端点

| 类型 | 名称 | URL |
|------|------|-----|
| telegram | miningrelease | https://t.me/s/miningrelease |
| yiimp_pool | zpool | https://zpool.ca/api/currencies |
| yiimp_pool | zergpool | https://zergpool.com/api/currencies |
| yiimp_pool | rplant | https://pool.rplant.xyz/api/currencies |
| yiimp_pool | gaelium | https://pool.gaelium.io/api/currencies |
| rss | reddit_gpumining | https://www.reddit.com/r/gpumining/new/.rss |
| rss | reddit_cryptomining | https://www.reddit.com/r/cryptomining/new/.rss |
| rss | reddit_search | https://www.reddit.com/search.rss?q=kawpow+OR+randomx+OR+%22fair+launch%22+OR+%22new+coin%22&sort=new |
| rss | twominers_blog | https://2miners.com/blog/feed/ |
| rss | hnrss_pow | https://hnrss.org/newest?q=pow+OR+kawpow+OR+randomx+OR+%22new+coin%22 |
| rss | litecointalk_ann | https://litecointalk.io/c/project-announcements/6.rss |
| rainbowminer | coinsdb | https://raw.githubusercontent.com/RainbowMiner/RainbowMiner/master/Data/coinsdb.json |
| coinpaprika | coins | https://api.coinpaprika.com/v1/coins |
| github_release | BTX | https://github.com/btxchain/btx/releases.atom |
| github_release | Parallax | https://github.com/ParallaxProtocol/parallax/releases.atom |
| github_release | BlockZero | https://github.com/Rexemre/blockzero-core/releases.atom |
| github_release | C64 Chain | https://github.com/oxynaz/c64chain-mainnet/releases.atom |
| github_release | Tensorium | https://github.com/tensorium-labs/tensorium-core/releases.atom |
| github_release | Irium | https://github.com/iriumlabs/irium/releases.atom |
| github_release | Gaelium | https://github.com/GaeliumCore/Gaelium/releases.atom |
| github_release | OggPoW Miner | https://github.com/Oggcoin/OggPoW-Miner/releases.atom |
| github_release | QSDM | https://github.com/blackbeardONE/QSDM/releases.atom |
| github_release | QUB Core | https://github.com/AlxProe/qub-core/releases.atom |
| exchange | xeggex | https://api.xeggex.com/api/v2/market/getlist |
| exchange | freiexchange | https://api.freiexchange.com/public/ticker |
| nicehash | algorithms | https://api2.nicehash.com/main/api/v2/mining/algorithms |
| bitcointalk | announcements | https://bitcointalk.org/index.php?board=159.0 |
| github_search | pow mining gpu created:>{since} | https://api.github.com/search/repositories?q=pow mining gpu created:>{since} |
| github_search | kawpow cryptocurrency created:>{since} | https://api.github.com/search/repositories?q=kawpow cryptocurrency created:>{since} |
| github_search | proof of work blockchain gpu created:>{since} | https://api.github.com/search/repositories?q=proof of work blockchain gpu created:>{since} |
| github_search | matmul mining created:>{since} | https://api.github.com/search/repositories?q=matmul mining created:>{since} |
| github_search | progpow miner created:>{since} | https://api.github.com/search/repositories?q=progpow miner created:>{since} |
| github_search | fair launch RandomX pushed:>{since} | https://api.github.com/search/repositories?q=fair launch RandomX pushed:>{since} |
| github_search | topic:proof-of-work pushed:>{since} | https://api.github.com/search/repositories?q=topic:proof-of-work pushed:>{since} |
| github_search | stratum genesis block reward in:readme created:>{since} | https://api.github.com/search/repositories?q=stratum genesis block reward in:readme created:>{since} |
| github_search | org:btxchain OR org:ParallaxProtocol pushed:>{since} | https://api.github.com/search/repositories?q=org:btxchain OR org:ParallaxProtocol pushed:>{since} |
| github_search | mainnet gpu mining created:>{since} | https://api.github.com/search/repositories?q=mainnet gpu mining created:>{since} |
| github_search | TensorHash mainnet created:>{since} | https://api.github.com/search/repositories?q=TensorHash mainnet created:>{since} |
| github_search | OggPoW mainnet created:>{since} | https://api.github.com/search/repositories?q=OggPoW mainnet created:>{since} |
| github_search | Gaelium kawpow created:>{since} | https://api.github.com/search/repositories?q=Gaelium kawpow created:>{since} |
| github_search | QSDM proof-of-work gpu created:>{since} | https://api.github.com/search/repositories?q=QSDM proof-of-work gpu created:>{since} |
| miningpoolstats | sitemap | https://miningpoolstats.stream/sitemap.xml |
| whattomine | coins | https://whattomine.com/coins.json |
| safetrade | home | https://safetrade.com/ |
| coingecko_search | pow mining | https://api.coingecko.com/api/v3/search?query=pow mining |
| coingecko_search | gpu mineable | https://api.coingecko.com/api/v3/search?query=gpu mineable |
| coingecko_search | kawpow | https://api.coingecko.com/api/v3/search?query=kawpow |
| generic_json | cryptunit | https://www.cryptunit.com/api/coins |
| generic_json | grandpool | https://api.grandpool.io/pools |
| generic_json | miningpoolhub | https://miningpoolhub.com/index.php?page=api&action=getminingandprofitsstatistics&api_key= |

## Agent 如何追加新来源

1. 验证 URL 可访问（HTTP 200 / 有效 RSS / JSON）
2. 写入 `config/discovered_sources.yaml` 对应列表
3. 运行 `./run.sh --dry-run` 验证
4. `git commit` + `git push`

无需改 Python 的类型：RSS、YiiMP 矿池 API、Telegram 频道、交易所 API、GitHub query/release、generic_json
