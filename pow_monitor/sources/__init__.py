from pow_monitor.sources.bitcointalk import fetch_bitcointalk
from pow_monitor.sources.coingecko import fetch_coingecko
from pow_monitor.sources.coinpaprika import fetch_coinpaprika
from pow_monitor.sources.exchanges import fetch_exchanges
from pow_monitor.sources.github_releases import fetch_github_releases
from pow_monitor.sources.github_search import fetch_github
from pow_monitor.sources.miningpoolstats import fetch_miningpoolstats
from pow_monitor.sources.nicehash import fetch_nicehash
from pow_monitor.sources.rainbowminer import fetch_rainbowminer
from pow_monitor.sources.rss_feeds import fetch_rss_feeds
from pow_monitor.sources.safetrade import fetch_safetrade
from pow_monitor.sources.telegram_public import fetch_telegram_public
from pow_monitor.sources.whattomine import fetch_whattomine
from pow_monitor.sources.yiimp_pools import fetch_yiimp_pools

__all__ = [
    "fetch_bitcointalk",
    "fetch_github",
    "fetch_github_releases",
    "fetch_miningpoolstats",
    "fetch_whattomine",
    "fetch_yiimp_pools",
    "fetch_rss_feeds",
    "fetch_telegram_public",
    "fetch_coinpaprika",
    "fetch_rainbowminer",
    "fetch_nicehash",
    "fetch_exchanges",
    "fetch_safetrade",
    "fetch_coingecko",
]
