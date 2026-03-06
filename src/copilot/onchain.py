from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class OnchainOSCLIError(RuntimeError):
    """Raised when interacting with the onchainos CLI fails."""


class OnchainOSCLI:
    def __init__(self, executable: str = "onchainos") -> None:
        self.executable = executable

    def available(self) -> bool:
        return shutil.which(self.executable) is not None

    def run(self, args: List[str]) -> Dict[str, Any]:
        if not self.available():
            raise OnchainOSCLIError(
                "onchainos CLI 未安装。运行 curl -sSL https://raw.githubusercontent.com/okx/onchainos-skills/main/install.sh | sh 安装。"
            )
        proc = subprocess.run(  # noqa: S603, S607
            [self.executable, *args],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise OnchainOSCLIError(proc.stderr.strip() or proc.stdout.strip() or "onchainos CLI 调用失败")
        output = proc.stdout.strip()
        if not output:
            return {}
        try:
            return json.loads(output)
        except json.JSONDecodeError as exc:
            raise OnchainOSCLIError(f"无法解析 onchainos 输出: {exc}") from exc


@dataclass
class TokenRoute:
    symbol: str
    chain: str
    address: str


TOKEN_REGISTRY: Dict[str, TokenRoute] = {
    "ETH": TokenRoute("ETH", "ethereum", "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"),
    "BTC": TokenRoute("BTC", "ethereum", "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"),  # WBTC
    "SOL": TokenRoute("SOL", "solana", "So11111111111111111111111111111111111111112"),
    "USDT": TokenRoute("USDT", "ethereum", "0xdac17f958d2ee523a2206206994597c13d831ec7"),
    "OKB": TokenRoute("OKB", "xlayer", "0xdf54c5c0f3e9abec9ce7d2d043c1a76ad1078d6d"),
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class OnchainOSClient:
    def __init__(self, cli: Optional[OnchainOSCLI] = None) -> None:
        self.cli = cli or OnchainOSCLI()
        self.last_error: Optional[str] = None

    # ------------------------------------------------------------------
    def market_snapshot(self, asset: str) -> Optional[Dict[str, Any]]:
        route = self._resolve_asset(asset)
        payload = self._call([
            "token",
            "price-info",
            route.address,
            "--chain",
            route.chain,
        ])
        if not payload:
            return None
        row = payload[0]
        price = _safe_float(row.get("price"))
        change = _safe_float(row.get("priceChange24H"))
        volume = _safe_float(row.get("volume24H")) / 1_000_000 if row.get("volume24H") else 0.0
        trend = "Bullish" if change > 0.5 else ("Bearish" if change < -0.5 else "Sideways")
        return {
            "price": price,
            "change_24h_pct": change,
            "vol_24h_musd": volume,
            "trend": trend,
            "source": "OnchainOS",
        }

    def trending_tokens(self, chain: str = "solana", limit: int = 3) -> Optional[List[Dict[str, Any]]]:
        payload = self._call([
            "token",
            "trending",
            "--chains",
            chain,
            "--sort-by",
            "5",
            "--time-frame",
            "4",
        ])
        if not payload:
            return None
        items: List[Dict[str, Any]] = []
        for row in payload[:limit]:
            items.append(
                {
                    "symbol": (row.get("tokenSymbol") or "-").upper(),
                    "change_pct": _safe_float(row.get("change")),
                    "volume_usd": _safe_float(row.get("volume")),
                    "market_cap": _safe_float(row.get("marketCap")),
                    "liquidity": _safe_float(row.get("liquidity")),
                    "address": row.get("tokenContractAddress"),
                    "holders": row.get("holders"),
                }
            )
        return items

    def gas_quote(self, chain: str = "ethereum", gas_limit: int = 21_000) -> Optional[Dict[str, Any]]:
        payload = self._call(["gateway", "gas", "--chain", chain])
        if not payload:
            return None
        row = payload[0]
        to_gwei = lambda x: _safe_float(x) / 1_000_000_000 if x is not None else 0.0
        min_gwei = to_gwei(row.get("min"))
        normal_gwei = to_gwei(row.get("normal"))
        max_gwei = to_gwei(row.get("max"))
        base_gwei = to_gwei(row.get("eip1559Protocol", {}).get("baseFee"))
        snapshot = self.market_snapshot("ETH") or {}
        eth_price = snapshot.get("price", 0.0) or 0.0
        est_usd = normal_gwei * (1e-9) * gas_limit * eth_price
        return {
            "chain": chain,
            "min_gwei": min_gwei,
            "normal_gwei": normal_gwei,
            "max_gwei": max_gwei,
            "base_gwei": base_gwei,
            "est_transfer_usd": est_usd,
            "supports_eip1559": bool(row.get("supportEip1559")),
        }

    # ------------------------------------------------------------------
    def _call(self, args: List[str]) -> Optional[List[Dict[str, Any]]]:
        try:
            payload = self.cli.run(args)
        except OnchainOSCLIError as exc:
            self.last_error = str(exc)
            return None
        data = payload.get("data")
        if not isinstance(data, list):
            return None
        return data

    def _resolve_asset(self, asset: str) -> TokenRoute:
        key = (asset or "ETH").upper()
        return TOKEN_REGISTRY.get(key, TOKEN_REGISTRY["ETH"])
