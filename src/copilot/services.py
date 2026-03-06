"""OnchainOS service layer wrapping the official CLI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .onchain import OnchainOSClient as _CLIClient


@dataclass
class MarketSnapshot:
    price: float
    change_24h_pct: float
    vol_24h_musd: float
    trend: str
    source: str = "OnchainOS"


_FALLBACK_TOPICS = [
    "EigenLayer restaking TVL 再创新高",
    "Solana memecoin 热度回潮",
    "Layer2 Gas 降费提案",
    "Modular 赛道融资",
    "Bitcoin Runes 交易量回升",
    "Base 链活跃用户破纪录",
]

_FALLBACK_WATCHLIST = [
    "ETH/BTC 长期相关性下降",
    "SOL 上破 200 美元关注回调",
    "SUI 生态空投窗口",
]


class OnchainOSClient:
    """High-level helper around the onchainos CLI."""

    def __init__(self, cli: Optional[_CLIClient] = None) -> None:
        self.cli = cli or _CLIClient()

    # ------------------------- Market ---------------------------------
    def market_snapshot(self, asset: str) -> MarketSnapshot:
        payload = self.cli.market_snapshot(asset)
        if not payload:
            return MarketSnapshot(price=2000.0, change_24h_pct=0.0, vol_24h_musd=120.0, trend="Sideways", source="Fallback")
        return MarketSnapshot(
            price=payload["price"],
            change_24h_pct=payload["change_24h_pct"],
            vol_24h_musd=payload["vol_24h_musd"],
            trend=payload["trend"],
            source=payload.get("source", "OnchainOS"),
        )

    # ------------------------- Content --------------------------------
    def trending_topics(self, count: int = 3, chain: str = "solana") -> List[str]:
        data = self.cli.trending_tokens(chain=chain, limit=count)
        if not data:
            return _FALLBACK_TOPICS[:count]
        topics: List[str] = []
        for row in data:
            vol_m = row.get("volume_usd", 0.0) / 1_000_000
            topics.append(
                f"{row['symbol']} · {row.get('change_pct', 0):+.2f}% · ${vol_m:.1f}M · {chain}"
            )
        return topics

    def watchlist_candidates(self, chain: str = "solana") -> List[str]:
        data = self.cli.trending_tokens(chain=chain, limit=5)
        if not data:
            return _FALLBACK_WATCHLIST
        watchlist = []
        for row in data:
            market_cap = row.get("market_cap", 0.0) / 1_000_000
            watchlist.append(f"{row['symbol']} · MCap ${market_cap:.1f}M")
        return watchlist

    # ------------------------- Payments --------------------------------
    def payment_quote(self, chain: str = "ethereum", token: str = "USDT", amount: float = 100.0) -> Dict[str, float]:
        gas = self.cli.gas_quote(chain=chain)
        if not gas:
            return {"gas_normal_gwei": 5.0, "est_transfer_usd": 0.2, "chain": chain}
        return {
            "chain": chain,
            "gas_normal_gwei": gas.get("normal_gwei", 0.0),
            "gas_min_gwei": gas.get("min_gwei", 0.0),
            "gas_max_gwei": gas.get("max_gwei", 0.0),
            "est_transfer_usd": gas.get("est_transfer_usd", 0.0),
            "supports_eip1559": gas.get("supports_eip1559", False),
            "base_gwei": gas.get("base_gwei", 0.0),
            "token": token,
            "amount": amount,
        }

    def compliance_scan(self, address: str) -> Dict[str, str]:
        flagged = address.lower().startswith("0xdead")
        return {"status": "blocked" if flagged else "clean", "source": "heuristic"}
