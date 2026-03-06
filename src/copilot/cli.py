"""Command-line driver for Onchain Copilot."""

from __future__ import annotations

import argparse
import json
from typing import Optional

from .intents import IntentParser
from .pipelines import PipelineBuilder
from .report import format_plan


def run_cli(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Onchain Copilot MVP CLI")
    parser.add_argument("--mode", choices=["trading", "operations", "payment"], help="强制选择一个场景")
    parser.add_argument("--text", help="直接传入的自然语言需求")
    parser.add_argument("--json", action="store_true", help="输出 JSON 原始数据")
    args = parser.parse_args(argv)

    if args.text:
        user_text = args.text.strip()
    else:
        placeholder = "示例：帮我分3笔买入ETH，总预算1000USDT，30分钟一笔，滑点不超过0.8%"
        user_text = input(f"请输入需求\n{placeholder}\n> ").strip()

    parser_service = IntentParser(default_mode=args.mode)
    parsed_intent = parser_service.parse(user_text)
    builder = PipelineBuilder()
    plan = builder.build(parsed_intent)

    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        print(format_plan(plan))


__all__ = ["run_cli"]
