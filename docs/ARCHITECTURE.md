# 架构概览

```
┌──────────┐   ┌────────────┐   ┌──────────────┐
│ Web/CLI │→│ IntentParser │→│ PipelineBuilder │→ JSON/Plan → UI
└──────────┘   └────────────┘   └──────────────┘
                         │
                         ▼
                 OnchainOSClient (mock)
```

## 模块说明
- `IntentParser`：基于关键词 + 正则的轻量意图解析器，支持交易 / 运营 / 支付三种场景自动识别。
- `PipelineBuilder`：按场景拼装执行步骤、风控检查、后续动作。调用 `OnchainOSClient` 获取行情、热点、支付 quote 等。
- `OnchainOSClient`：当前为模拟层，后续替换为真实 OnchainOS API/SDK。
- `report.format_plan`：CLI 文本渲染；Web 直接消费 JSON。

## 与 OnchainOS 的映射
| 模块 | OnchainOS 能力 | 状态 |
| --- | --- | --- |
| MarketSnapshot | 行情/资产接口 | ✅ Mock，待接正式 API |
| Trading Pipeline | 钱包余额 + DEX 交易 | 🟡 已预留接口 |
| Operations Pipeline | 内容/数据 API、Watchlist、通知 | 🟡 待接数据源 |
| Payment Pipeline | 钱包、支付、风控、DApp | 🟡 预留 |

## 扩展点
1. **真实 API**：把 `services.py` 中的模拟函数替换为 OnchainOS SDK 调用。
2. **策略插件**：`PipelineBuilder` 引入策略/风控插件机制，支持扩展更多版本。
3. **事件流**：计划 → 执行 → 复盘 的状态同步，可写入数据库或消息总线。
4. **前端**：将当前静态 Web Demo 升级为 React/Next.js + API。
