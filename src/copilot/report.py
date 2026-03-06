"""Formatting helpers for CLI output."""

from __future__ import annotations

from typing import Dict, List


def format_plan(plan: Dict) -> str:
    lines: List[str] = []
    lines.append(f"场景：{plan['scenario']} · {plan['title']}")
    lines.append(f"摘要：{plan['summary']}")
    if plan.get("market"):
        market = plan["market"]
        lines.append(
            f"行情：{market['price']} ({market['change_24h_pct']}% / {market['trend']}) · 24h量 {market['vol_24h_musd']}M"
        )
    lines.append("\n执行步骤：")
    for step in plan["steps"]:
        detail = []
        if step.get("amount_usdt"):
            detail.append(f"{step['amount_usdt']} USDT")
        if step.get("delay_min") is not None:
            detail.append(f"T+{step['delay_min']}min")
        if step.get("output"):
            detail.append(", ".join(step["output"]))
        if step.get("details"):
            detail.append(", ".join(f"{k}:{v}" for k, v in step["details"].items()))
        if step.get("checks"):
            detail.append(f"检查: {', '.join(step['checks'])}")
        detail_str = " | ".join(detail) if detail else ""
        lines.append(f"  #{step['id']} {step['action']} {detail_str}")
    lines.append("\n风控检查：")
    for item in plan["risk"]:
        lines.append(f"  - {item['name']}: {item['value']} ({item['status']})")
    if plan.get("follow_up"):
        lines.append("\n后续动作：")
        for item in plan["follow_up"]:
            lines.append(f"  - {item}")
    return "\n".join(lines)
