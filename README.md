# Onchain Copilot（链上副驾驶）

> 自然语言 → 链上执行完整链路：看行情 → 出策略 → 风控检查 → 一键执行 → 自动复盘。

## 产品定位
- **MVP 目标**：在 7 天内交付可以演示的多场景链上副驾驶，凸显 OnchainOS 钱包/交易/行情/支付/DApp 能力。
- **一句话**：用户只要描述需求，Agent 负责拆解、规划、风控、执行与复盘。

### 最适合落地的 3 个版本
| 版本 | 描述 | 示例意图 |
| --- | --- | --- |
| 交易版 | 分批下单 + 风控最易出效果 | “帮我分 3 笔买入 ETH，回撤 5% 停手” |
| 运营版 | 运营自动抓热点 + 内容 + 交易观察 | “抓 3 个热点并生成 X 可发内容 + 关联观察” |
| 支付版 | 安全便捷的链上支付/打款 | “给地址 A 打 100 USDT，gas 超阈值就延后” |

## 快速开始
### 1. CLI
```bash
cd onchain-copilot
python3 src/copilot.py --mode trading --text "帮我分3笔买入ETH，总预算1000USDT，30分钟一笔，滑点不超过0.8%"
python3 src/copilot.py --mode operations --text "抓 3 个热点做 X 帖子，并附上交易观察"
python3 src/copilot.py --mode payment --text "给 0xabc... 打 100 USDT，gas 超 8 USDT 延后"
```
- `--mode` 可选 `trading / operations / payment`，不传则自动识别。
- `--json` 可输出完整 JSON，用于前端或 API。

### 2. Web Demo
```bash
cd onchain-copilot
python3 -m http.server 8787
# 打开 http://localhost:8787 演示多场景计划
```
浏览器端支持：场景切换、示例提示、执行动画以及 JSON 导出。

### 3. OnchainOS 实时数据接入
1. 安装官方 CLI（一次性）
   ```bash
   curl -sSL https://raw.githubusercontent.com/okx/onchainos-skills/main/install.sh | sh
   onchainos --version
   ```
2. （可选）配置私有 API Key：复制 `.env.example` 为 `.env`，写入 `OKX_API_KEY / OKX_SECRET_KEY / OKX_PASSPHRASE`。默认会使用官方提供的沙盒 Key。
3. CLI & Web Demo 会实时调用 `onchainos` 获取行情、热点、Gas 估算等数据。

### 4. 轻量后端 API（FastAPI）
```bash
cd onchain-copilot
pip install -r requirements.txt
uvicorn api.server:app --reload  # 默认端口 8000
```
- POST `http://localhost:8000/plan`，Body：`{ "text": "帮我分3笔买入ETH...", "mode": "trading" }`
- 返回值即 CLI/Web Demo 使用的 JSON 结构，可直接被前端调用。
- 记得先安装 OnchainOS CLI（见上一步），后端会复用同一套实时数据。

## 目录结构
```
onchain-copilot/
├── README.md
├── index.html              # Web Demo 入口（可直接 GitHub Pages 部署）
├── styles.css
├── app.js
├── requirements.txt        # FastAPI / Uvicorn
├── .env.example            # OnchainOS API Key 模板（勿提交真实 .env）
├── api/
│   └── server.py           # FastAPI 轻量后端
├── docs/
│   ├── PRD.md              # 产品需求 & 赛题映射
│   ├── DEMO_SCRIPT.md      # 90s 演示脚本（多场景）
│   ├── SUBMISSION_DRAFT.md # 参赛投稿草稿
│   ├── VERSIONS.md         # 三个版本的详细拆解
│   └── ARCHITECTURE.md     # 技术架构与对 OnchainOS 的映射
└── src/
    ├── copilot.py          # CLI 入口
    └── copilot/            # 意图解析 + Pipeline + OnchainOS 封装
```

## 当前进度（V2）
- [x] 产品定义、版本拆解与演示脚本
- [x] 意图解析：交易 / 运营 / 支付 场景自动识别
- [x] Pipeline：生成执行步骤 + 风控清单 + 跟进动作
- [x] CLI + Web Demo（可切换场景 + JSON 输出）
- [x] 接入 OnchainOS CLI：行情快照 / 热点榜单 / Gas 估算
- [ ] 风控规则引擎（仓位、滑点、Gas、黑名单）
- [ ] Demo 视频 + 参赛物料

## 下一步
1. **执行链路打通**：在现有行情/热点/Gas 的基础上，接入 swap / broadcast / wallet balance 等 OnchainOS 命令，完成可签名的真实交易链路。
2. **策略/风控插件化**：每个步骤支持策略模板和自定义指标。
3. **DApp 编排**：在 DEX、支付、借贷间组装多步骤工作流。
4. **回测与复盘**：落库实际执行日志，给出可解释的复盘报告。

欢迎在 GitHub（私有/内部）托管，后续接入 CI、真实 API、以及 Demo 录制素材。🦞
