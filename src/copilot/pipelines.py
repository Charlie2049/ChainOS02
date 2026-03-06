"""Execution plan builder for different scenarios."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List

from .intents import ParsedIntent
from .services import OnchainOSClient


class PipelineBuilder:
    def __init__(self, client: OnchainOSClient | None = None) -> None:
        self.client = client or OnchainOSClient()

    def build(self, intent: ParsedIntent) -> Dict[str, Any]:
        if intent.scenario == "operations":
            return self._build_operations(intent)
        if intent.scenario == "payment":
            return self._build_payment(intent)
        return self._build_trading(intent)

    # ------------------------------------------------------------------
    def _build_trading(self, intent: ParsedIntent) -> Dict[str, Any]:
        params = intent.parameters
        snapshot = self.client.market_snapshot(params["asset"])
        tranches = params["tranches"]
        per = round(params["budget_usdt"] / tranches, 2)
        steps = []
        for idx in range(tranches):
            delay = idx * params["interval_min"]
            amount = per if idx < tranches - 1 else round(params["budget_usdt"] - per * (tranches - 1), 2)
            steps.append(
                {
                    "id": idx + 1,
                    "action": f"{params['side']} {params['asset']}",
                    "amount_usdt": amount,
                    "delay_min": delay,
                    "checks": ["slippage", "twap"],
                }
            )
        risk = [
            {
                "name": "Slippage",
                "value": f"≤ {params['max_slippage_pct']}%",
                "status": "OK",
            },
            {
                "name": "Drawdown",
                "value": f"停手阈值 {params['max_drawdown_pct']}%",
                "status": "OK",
            },
            {
                "name": "Market",
                "value": f"24h 变化 {snapshot.change_24h_pct:+.2f}%",
                "status": "Watch" if abs(snapshot.change_24h_pct) > 5 else "OK",
            },
        ]
        follow_up = [
            "24h 复盘：成交均价 vs. 市场中位价",
            "推送：若波动 > 阈值自动暂停",
        ]
        return {
            "scenario": intent.scenario,
            "title": "分批交易计划",
            "summary": intent.summary,
            "intent": params,
            "market": asdict(snapshot),
            "steps": steps,
            "risk": risk,
            "follow_up": follow_up,
        }

    def _build_operations(self, intent: ParsedIntent) -> Dict[str, Any]:
        params = intent.parameters
        topics = self.client.trending_topics(params["topics"], chain=params["chain"])
        watchlist = self.client.watchlist_candidates(chain=params["chain"]) if params["include_watchlist"] else []
        steps = [
            {
                "id": 1,
                "action": f"抓取 {params['chain']} 热点",
                "output": topics,
            },
            {
                "id": 2,
                "action": f"生成 {params['channel']} 可发内容",
                "output": [f"[{t}] 情绪摘要 + CTA" for t in topics],
            },
        ]
        if watchlist:
            steps.append(
                {
                    "id": 3,
                    "action": "交易观察",
                    "output": watchlist,
                }
            )
        risk = [
            {"name": "事实核验", "status": "Pending human", "value": "AI 草稿需人工确认"},
            {"name": "交易免责声明", "status": "Auto", "value": "默认附带"},
        ]
        follow_up = [
            f"{params['cadence']} 回顾互动数据",
            "热点 → 内容 → 交易观察 三合一归档",
        ]
        return {
            "scenario": intent.scenario,
            "title": "运营热点工作流",
            "summary": intent.summary,
            "intent": params,
            "steps": steps,
            "risk": risk,
            "follow_up": follow_up,
        }

    def _build_payment(self, intent: ParsedIntent) -> Dict[str, Any]:
        params = intent.parameters
        quote = self.client.payment_quote(chain=params["chain"], token=params["token"], amount=params["amount"])
        compliance = self.client.compliance_scan(params["recipient"])
        steps = [
            {
                "id": 1,
                "action": f"Gas 状态（{params['chain']})",
                "details": {
                    "normal_gwei": quote.get("gas_normal_gwei"),
                    "min_gwei": quote.get("gas_min_gwei"),
                    "max_gwei": quote.get("gas_max_gwei"),
                    "est_transfer_usd": quote.get("est_transfer_usd"),
                    "eip1559": quote.get("supports_eip1559"),
                },
            },
            {
                "id": 2,
                "action": "Compliance",
                "details": compliance,
            },
            {
                "id": 3,
                "action": "Sign & Broadcast",
                "details": {
                    "max_gas_usd": params["max_gas_usd"],
                    "priority": params["priority"],
                    "chain": params["chain"],
                },
            },
        ]
        risk = [
            {
                "name": "Gas 估算",
                "value": f"≈ ${quote.get('est_transfer_usd', 0):.2f} / 阈值 {params['max_gas_usd']} USDT",
                "status": "OK" if quote.get("est_transfer_usd", 0) <= params["max_gas_usd"] else "Hold",
            },
            {
                "name": "Compliance",
                "value": compliance["status"],
                "status": "OK" if compliance["status"] == "clean" else "Blocked",
            },
        ]
        follow_up = ["生成支付回执 + 自动记账"]
        return {
            "scenario": intent.scenario,
            "title": "链上支付助手",
            "summary": intent.summary,
            "intent": params,
            "steps": steps,
            "risk": risk,
            "follow_up": follow_up,
        }
