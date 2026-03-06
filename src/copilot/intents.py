"""Intent parsing utilities for Onchain Copilot."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional

Scenario = Literal["trading", "operations", "payment"]


@dataclass
class ParsedIntent:
    """Normalized intent after parsing natural language."""

    scenario: Scenario
    summary: str
    parameters: Dict[str, Any] = field(default_factory=dict)


class IntentParser:
    """Very lightweight rule-based parser for MVP demos."""

    def __init__(self, default_mode: Optional[Scenario] = None) -> None:
        self.default_mode = default_mode

    def parse(self, text: str) -> ParsedIntent:
        text = text.strip()
        lowered = text.lower()
        scenario = self._detect_scenario(lowered)
        if self.default_mode:
            scenario = self.default_mode

        if scenario == "operations":
            return self._parse_operations(text, lowered)
        if scenario == "payment":
            return self._parse_payment(text, lowered)
        return self._parse_trading(text, lowered)

    # --- Scenario detection -------------------------------------------------
    def _detect_scenario(self, lowered: str) -> Scenario:
        if any(k in lowered for k in ["打", "转", "transfer", "send", "address", "usdt", "payment"]):
            if "内容" in lowered or "tweet" in lowered:
                # tweet about payments? fall back to detection order
                pass
            else:
                if "运营" not in lowered and "热点" not in lowered:
                    return "payment"
        if any(k in lowered for k in ["热点", "内容", "tweet", "运营", "观察", "x账号", "帖子"]):
            return "operations"
        return "trading"

    # --- Trading ------------------------------------------------------------
    def _parse_trading(self, text: str, lowered: str) -> ParsedIntent:
        asset = self._extract_asset(lowered)
        side = "SELL" if any(k in lowered for k in ["卖", "sell", "reduce"]) else "BUY"
        budget = self._extract_float(lowered, r"(\d+(?:\.\d+)?)\s*(?:usdt|usd|u)", default=1000.0)
        tranches = int(self._extract_float(text, r"分\s*(\d+)\s*笔|in\s*(\d+)\s*parts?", default=3))
        interval = self._extract_interval(text)
        slippage = self._extract_float(text, r"(?:滑点|slippage)[^\d]*(\d+(?:\.\d+)?)\s*%", default=0.8)
        stop_loss = self._extract_float(text, r"(?:回撤|止损|stop)\D*(\d+(?:\.\d+)?)\s*%", default=5.0)
        chain = self._detect_chain_hint(lowered)
        if asset == "SOL":
            chain = "solana"
        summary = f"{side} {asset} in {tranches} tranches with {budget} USDT budget"
        params = {
            "asset": asset,
            "side": side,
            "budget_usdt": budget,
            "tranches": tranches,
            "interval_min": interval,
            "max_slippage_pct": slippage,
            "max_drawdown_pct": stop_loss,
            "chain": chain,
        }
        return ParsedIntent("trading", summary, params)

    # --- Operations ---------------------------------------------------------
    def _parse_operations(self, text: str, lowered: str) -> ParsedIntent:
        topics = int(self._extract_float(text, r"(\d+)\s*(?:个)?(?:热点|topic|条)", default=3))
        channel = "X"
        if "小红书" in text:
            channel = "Xiaohongshu"
        elif "微博" in text or "weibo" in lowered:
            channel = "Weibo"
        watch = bool(re.search(r"交易|观察|watch", text, re.IGNORECASE))
        cadence = "每日"
        if "每周" in text or "weekly" in lowered:
            cadence = "每周"
        chain = self._detect_chain_hint(lowered)
        summary = f"{chain} hot topics x {cadence} cadence"
        params = {
            "topics": topics,
            "channel": channel,
            "include_watchlist": watch,
            "cadence": cadence,
            "chain": chain,
        }
        return ParsedIntent("operations", summary, params)

    # --- Payment ------------------------------------------------------------
    def _parse_payment(self, text: str, lowered: str) -> ParsedIntent:
        amount = self._extract_float(lowered, r"(\d+(?:\.\d+)?)\s*(?:usdt|usd|eth|usdc)", default=100.0)
        token = self._extract_token(text)
        recipient_match = re.search(r"(0x[a-fA-F0-9]{6,}|addr\w+)", text)
        recipient = recipient_match.group(1) if recipient_match else "0xABCD...1234"
        gas_threshold = self._extract_float(text, r"gas[^\d]*(\d+(?:\.\d+)?)", default=8.0)
        priority = "defer" if any(k in lowered for k in ["延后", "delay", "wait"]) else "normal"
        chain = self._detect_chain_hint(lowered)
        summary = f"Transfer {amount} {token} to {recipient[:10]}... on {chain}"
        params = {
            "amount": amount,
            "token": token,
            "recipient": recipient,
            "max_gas_usd": gas_threshold,
            "priority": priority,
            "chain": chain,
        }
        return ParsedIntent("payment", summary, params)

    # --- Helpers ------------------------------------------------------------
    def _extract_asset(self, lowered: str) -> str:
        if "btc" in lowered:
            return "BTC"
        if "sol" in lowered:
            return "SOL"
        if "sui" in lowered:
            return "SUI"
        return "ETH"

    def _extract_token(self, text: str) -> str:
        tokens = ["usdt", "usdc", "eth", "btc", "sol", "sui", "okb"]
        lowered = text.lower()
        for tk in tokens:
            if tk in lowered:
                return tk.upper()
        return "USDT"

    def _extract_float(self, text: str, pattern: str, default: float) -> float:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return float(default)
        # support optional second capture group
        number = next((grp for grp in match.groups() if grp), None)
        return float(number) if number else float(default)

    def _extract_interval(self, text: str) -> int:
        match = re.search(r"(\d+)\s*(?:分钟|min)", text)
        if match:
            return int(match.group(1))
        match = re.search(r"(\d+)\s*(?:小时|hour|h)", text, re.IGNORECASE)
        if match:
            return int(match.group(1)) * 60
        return 30

    def _detect_chain_hint(self, lowered: str) -> str:
        lowered = lowered.lower()
        if any(k in lowered for k in ["sol", "solana", "索拉"]):
            return "solana"
        if any(k in lowered for k in ["bsc", "bnb"]):
            return "bsc"
        if any(k in lowered for k in ["polygon", "matic"]):
            return "polygon"
        if any(k in lowered for k in ["arbitrum", "arb"]):
            return "arbitrum"
        if "base" in lowered:
            return "base"
        if any(k in lowered for k in ["xlayer", "okb", "okx"]):
            return "xlayer"
        return "ethereum"
