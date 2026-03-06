"""Mocked OnchainOS service layer for the MVP."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class MarketSnapshot:
    price: float
    change_24h_pct: float
    vol_24h_musd: float
    trend: str


class OnchainOSClient:
    """A lightweight simulator standing in for real OnchainOS APIs."""

    def __init__(self) -> None:
        self._bases = {
            "ETH": 3420,
            "BTC": 61200,
            "SOL": 128,
            "SUI": 1.6,
        }

    # ------------------------- Market -------------------------------------
    def market_snapshot(self, asset: str) -> MarketSnapshot:
        rng = self._rng(f"market:{asset}")
        base = self._bases.get(asset, 100)
        price = round(base * (0.94 + rng.random() * 0.12), 2)
        change = round(rng.uniform(-4, 4), 2)
        vol = round(rng.uniform(50, 200), 1)
        trend = "Bullish" if change > 0.5 else ("Bearish" if change < -0.5 else "Sideways")
        return MarketSnapshot(price, change, vol, trend)

    # ------------------------- Content ------------------------------------
    def trending_topics(self, count: int = 3) -> List[str]:
        topics = [
            "EigenLayer restaking TVL 再创新高",
            "Solana memecoin 热度回潮",
            "Layer2 Gas 降费提案",
            "Modular 赛道融资",
            "Bitcoin Runes 交易量回升",
            "Base 链活跃用户破纪录",
        ]
        rng = self._rng("topics")
        rng.shuffle(topics)
        return topics[:count]

    def watchlist_candidates(self) -> List[str]:
        return [
            "ETH/BTC 长期相关性下降",
            "SOL 上破 200 美元关注回调",
            "SUI 生态空投窗口",
        ]

    # ------------------------- Payments -----------------------------------
    def payment_quote(self, token: str, amount: float) -> Dict[str, float]:
        rng = self._rng(f"pay:{token}:{amount}")
        gas = round(rng.uniform(3, 9), 2)
        ETA = "< 1 min" if gas > 5 else "~3 min"
        return {"gas_usd": gas, "eta": ETA}

    def compliance_scan(self, address: str) -> Dict[str, str]:
        flagged = address.lower().startswith("0xdead")
        return {"status": "blocked" if flagged else "clean", "source": "MockChain"}

    # ------------------------- Helpers ------------------------------------
    def _rng(self, key: str) -> random.Random:
        digest = hashlib.sha256(key.encode()).hexdigest()
        seed = int(digest[:16], 16)
        return random.Random(seed)
