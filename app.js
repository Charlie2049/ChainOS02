const samples = {
  trading: '帮我分3笔买入ETH，总预算1000USDT，30分钟一笔，滑点不超过0.8%，回撤5%停手。',
  operations: '抓 3 个 Crypto 热点，生成 X 可发内容，并附交易观察提醒。',
  payment: '给 0xAbC12345... 打 100 USDT，gas 超 8 USDT 就延后执行。'
};

let selectedScenario = 'trading';
let currentPlan = null;

const scenarioButtons = document.querySelectorAll('[data-scenario]');
const promptTextarea = document.getElementById('prompt');
const generateBtn = document.getElementById('generate');
const resetBtn = document.getElementById('reset');
const quickPrompts = document.getElementById('quick-prompts');
const statusTitle = document.getElementById('statusTitle');
const statusMeta = document.getElementById('statusMeta');
const intentBlock = document.getElementById('intentBlock');
const riskBlock = document.getElementById('riskBlock');
const stepsBlock = document.getElementById('stepsBlock');
const followBlock = document.getElementById('followBlock');
const jsonOutput = document.getElementById('jsonOutput');

function setScenario(value) {
  selectedScenario = value;
  scenarioButtons.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.scenario === value);
  });
  if (value !== 'auto') {
    promptTextarea.value = samples[value];
  }
}

scenarioButtons.forEach(btn => {
  btn.addEventListener('click', () => setScenario(btn.dataset.scenario));
});

quickPrompts.addEventListener('click', (event) => {
  if (event.target.dataset.prompt) {
    promptTextarea.value = event.target.dataset.prompt;
  }
});

resetBtn.addEventListener('click', () => {
  promptTextarea.value = samples[selectedScenario] || samples.trading;
  currentPlan = null;
  statusTitle.textContent = '尚未生成计划';
  statusMeta.textContent = '点击“生成计划”开始。';
  intentBlock.innerHTML = '';
  riskBlock.innerHTML = '';
  stepsBlock.innerHTML = '';
  followBlock.innerHTML = '';
  jsonOutput.textContent = '{}';
});

function detectScenario(text) {
  const lower = text.toLowerCase();
  if (/0x[a-f0-9]{6,}/i.test(text) || /(打|转|gas|address|transfer|send)/i.test(text)) {
    if (/(热点|内容|tweet|运营|post)/.test(text)) {
      return 'operations';
    }
    return 'payment';
  }
  if (/(热点|内容|tweet|运营|观察|post|thread)/.test(text)) {
    return 'operations';
  }
  return 'trading';
}

function parseTradingIntent(text) {
  const lower = text.toLowerCase();
  const intent = {
    asset: 'ETH',
    side: lower.includes('卖') || lower.includes('sell') ? 'SELL' : 'BUY',
    budget_usdt: 1000,
    tranches: 3,
    interval_min: 30,
    max_slippage_pct: 0.8,
    max_drawdown_pct: 5
  };
  if (lower.includes('btc')) intent.asset = 'BTC';
  if (lower.includes('sol')) intent.asset = 'SOL';
  const mBudget = lower.match(/(\d+(?:\.\d+)?)\s*(usdt|usd|u)/); if (mBudget) intent.budget_usdt = Number(mBudget[1]);
  const mTr = text.match(/(?:分|in\s*)(\d+)\s*(?:笔|parts?)/i); if (mTr) intent.tranches = Number(mTr[1]);
  const mInt = text.match(/(\d+)\s*(?:分钟|min)/i); if (mInt) intent.interval_min = Number(mInt[1]);
  const mSlip = text.match(/(?:滑点|slippage)[^\d]*(\d+(?:\.\d+)?)\s*%/i); if (mSlip) intent.max_slippage_pct = Number(mSlip[1]);
  const mDraw = text.match(/(?:回撤|止损|stop)[^\d]*(\d+(?:\.\d+)?)\s*%/i); if (mDraw) intent.max_drawdown_pct = Number(mDraw[1]);
  return intent;
}

function parseOperationsIntent(text) {
  const intent = {
    topics: 3,
    channel: /小红书/.test(text) ? 'Xiaohongshu' : 'X',
    include_watchlist: /(交易|观察|watch)/i.test(text),
    cadence: /(每周|weekly)/i.test(text) ? '每周' : '每日'
  };
  const mTopics = text.match(/(\d+)\s*(?:个)?(?:热点|topic|条)/i); if (mTopics) intent.topics = Number(mTopics[1]);
  return intent;
}

function parsePaymentIntent(text) {
  const lower = text.toLowerCase();
  const intent = {
    amount: 100,
    token: 'USDT',
    recipient: '0xABCD...1234',
    max_gas_usd: 8,
    priority: /(延后|delay)/.test(text) ? 'defer' : 'normal'
  };
  const amountMatch = lower.match(/(\d+(?:\.\d+)?)\s*(usdt|usd|usdc|eth)/);
  if (amountMatch) intent.amount = Number(amountMatch[1]);
  const tokenMatch = lower.match(/(usdt|usdc|eth|btc|sol|sui)/);
  if (tokenMatch) intent.token = tokenMatch[1].toUpperCase();
  const addrMatch = text.match(/0x[a-fA-F0-9]{6,}/);
  if (addrMatch) intent.recipient = addrMatch[0];
  const gasMatch = text.match(/gas[^\d]*(\d+(?:\.\d+)?)/i);
  if (gasMatch) intent.max_gas_usd = Number(gasMatch[1]);
  return intent;
}

function marketSnapshot(asset) {
  const base = { ETH: 3420, BTC: 61200, SOL: 128, SUI: 1.6 };
  const price = base[asset] || 100;
  const change = asset === 'BTC' ? 1.2 : -0.6;
  return {
    price,
    change_24h_pct: change,
    vol_24h_musd: asset === 'SOL' ? 92 : 140,
    trend: change > 0 ? 'Bullish' : 'Sideways'
  };
}

function buildTradingPlan(intent) {
  const per = +(intent.budget_usdt / intent.tranches).toFixed(2);
  const steps = [];
  for (let idx = 0; idx < intent.tranches; idx++) {
    const amount = idx === intent.tranches - 1 ? +(intent.budget_usdt - per * (intent.tranches - 1)).toFixed(2) : per;
    steps.push({
      id: idx + 1,
      action: `${intent.side} ${intent.asset}`,
      amount_usdt: amount,
      delay_min: idx * intent.interval_min,
      checks: ['slippage', 'twap']
    });
  }
  return {
    scenario: 'trading',
    title: '分批交易计划',
    summary: `${intent.side} ${intent.asset} · ${intent.tranches} 笔 / ${intent.budget_usdt} USDT`,
    intent,
    market: marketSnapshot(intent.asset),
    steps,
    risk: [
      { name: 'Slippage', value: `≤ ${intent.max_slippage_pct}%`, status: 'OK' },
      { name: 'Drawdown', value: `回撤 ${intent.max_drawdown_pct}% 停手`, status: 'OK' },
      { name: 'Gas', value: '< 5 USDT', status: 'OK' }
    ],
    follow_up: ['24h 复盘：成交均价 vs. 市场', '波动超阈值自动暂停']
  };
}

const topicsPool = [
  'EigenLayer TVL 再创高',
  'Solana memecoin 热度',
  'Layer2 降费提案',
  'Bitcoin Runes 交易量',
  'Base 链用户数破纪录',
  'Modular 赛道融资'
];

function sampleTopics(count) {
  const list = [...topicsPool];
  list.sort(() => Math.random() - 0.5);
  return list.slice(0, count);
}

function buildOperationsPlan(intent) {
  const topics = sampleTopics(intent.topics);
  const watchlist = intent.include_watchlist ? ['ETH/BTC 相关性下降', 'SOL 200 美元关注回调', 'SUI 生态空投窗口'] : [];
  const steps = [
    { id: 1, action: '抓取热点', output: topics },
    { id: 2, action: `生成 ${intent.channel} 可发内容`, output: topics.map(t => `${t} · CTA + 观点`) }
  ];
  if (watchlist.length) {
    steps.push({ id: steps.length + 1, action: '交易观察', output: watchlist });
  }
  return {
    scenario: 'operations',
    title: '运营热点工作流',
    summary: `热点 ${intent.topics} 个 · ${intent.channel} · ${intent.cadence}`,
    intent,
    steps,
    risk: [
      { name: '事实核验', value: 'AI 草稿需人工确认', status: 'Pending' },
      { name: '免责声明', value: '默认附带', status: 'Auto' }
    ],
    follow_up: [`${intent.cadence} 回顾互动数据`, '热点/内容/观察一体归档']
  };
}

function buildPaymentPlan(intent) {
  const quote = { gas_usd: 5.8, eta: '< 2 min' };
  const compliance = intent.recipient.toLowerCase().startsWith('0xdead') ? 'blocked' : 'clean';
  return {
    scenario: 'payment',
    title: '链上支付助手',
    summary: `向 ${intent.recipient.slice(0, 10)}... 转 ${intent.amount} ${intent.token}`,
    intent,
    steps: [
      { id: 1, action: 'Quote', details: quote },
      { id: 2, action: 'Compliance', details: { status: compliance } },
      { id: 3, action: 'Sign & Broadcast', details: { priority: intent.priority, max_gas: intent.max_gas_usd } }
    ],
    risk: [
      { name: 'Gas cap', value: `${quote.gas_usd}/${intent.max_gas_usd} USDT`, status: quote.gas_usd <= intent.max_gas_usd ? 'OK' : 'Hold' },
      { name: 'Compliance', value: compliance, status: compliance === 'clean' ? 'OK' : 'Blocked' }
    ],
    follow_up: ['生成支付回执 + 自动记账']
  };
}

function buildPlan(text, forcedScenario) {
  const scenario = forcedScenario === 'auto' ? detectScenario(text) : forcedScenario;
  if (scenario === 'operations') return buildOperationsPlan(parseOperationsIntent(text));
  if (scenario === 'payment') return buildPaymentPlan(parsePaymentIntent(text));
  return buildTradingPlan(parseTradingIntent(text));
}

function kvHtml(obj) {
  return Object.entries(obj).map(([k, v]) => `<div><span>${k}</span><strong>${formatValue(v)}</strong></div>`).join('');
}

function formatValue(v) {
  if (Array.isArray(v)) return v.join(', ');
  if (typeof v === 'object' && v !== null) return JSON.stringify(v);
  return v;
}

function render(plan) {
  statusTitle.textContent = plan.title || '等待输入';
  const summary = [];
  if (plan.summary) summary.push(plan.summary);
  if (plan.market) {
    summary.push(`行情：${plan.market.price} (${plan.market.change_24h_pct}% / ${plan.market.trend})`);
  }
  statusMeta.textContent = summary.length ? summary.join(' · ') : '请输入需求后生成计划';
  intentBlock.innerHTML = Object.keys(plan.intent || {}).length ? kvHtml(plan.intent) : '<p>等待解析...</p>';
  const riskList = plan.risk || [];
  riskBlock.innerHTML = riskList.length ? riskList.map(item => `<div><span>${item.name}</span><strong>${item.value} (${item.status})</strong></div>`).join('') : '<p>暂无风控检查</p>';
  stepsBlock.innerHTML = plan.steps.map(step => {
    const meta = [];
    if (step.amount_usdt) meta.push(`${step.amount_usdt} USDT`);
    if (typeof step.delay_min === 'number') meta.push(`T+${step.delay_min}m`);
    if (step.output) meta.push(step.output.join('；'));
    if (step.details) meta.push(Object.entries(step.details).map(([k, v]) => `${k}: ${v}`).join(', '));
    if (step.checks) meta.push(`检查: ${step.checks.join(', ')}`);
    return `<div class="step"><h5>#${step.id} ${step.action}</h5><p>${meta.join(' | ') || '...'}</p></div>`;
  }).join('') : '<p>暂无执行步骤。</p>';
  const follow = plan.follow_up || [];
  followBlock.innerHTML = follow.length ? follow.map(item => `<li>${item}</li>`).join('') : '<li>等待生成计划</li>';
  jsonOutput.textContent = JSON.stringify(plan, null, 2);
}

generateBtn.addEventListener('click', () => {
  const scenario = selectedScenario;
  const plan = buildPlan(promptTextarea.value.trim(), scenario);
  currentPlan = plan;
  render(plan);
});

// Initialize
setScenario('trading');
render({
  title: '等待输入',
  summary: '请输入需求后生成计划',
  intent: {},
  risk: [],
  steps: [],
  follow_up: []
});
