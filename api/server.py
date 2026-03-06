from __future__ import annotations

from pathlib import Path
import sys
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Ensure we can import from src/
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from copilot.intents import IntentParser  # type: ignore  # noqa: E402
from copilot.pipelines import PipelineBuilder  # type: ignore  # noqa: E402

app = FastAPI(
    title="Onchain Copilot API",
    description="Lightweight API wrapper around the CLI pipeline",
    version="0.1.0",
)


class PlanRequest(BaseModel):
    text: str = Field(..., description="自然语言需求")
    mode: Optional[Literal["trading", "operations", "payment"]] = Field(
        default=None, description="强制场景（可选）"
    )
    json_output: bool = Field(
        default=True,
        description="返回完整 JSON（默认 true，仅预留）",
    )


class PlanResponse(BaseModel):
    scenario: str
    title: str
    summary: str
    intent: dict
    steps: list
    risk: list
    follow_up: list | None = None
    market: Optional[dict] = None


parser_service = IntentParser()
builder = PipelineBuilder()


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/plan", response_model=PlanResponse)
def generate_plan(payload: PlanRequest) -> PlanResponse:
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="text 不能为空")

    parser = IntentParser(default_mode=payload.mode)
    parsed_intent = parser.parse(payload.text)
    plan = builder.build(parsed_intent)
    return PlanResponse(**plan)
