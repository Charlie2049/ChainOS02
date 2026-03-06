const el = (id) => document.getElementById(id);

const samples = {
  trading: '帮我分3笔买入ETH，总预算1000USDT，30分钟一笔，滑点不超过0.8%，回撤5%暂停',
  operations: '抓 3 个 Crypto 热点，生成 X 可发内容，并附交易观察提醒',
  payment: '给 0xAbC123... 打 100 USDT，gas 超 8 USDT 就延后执行',
};

const i18n = {
  zh: {
    subtitle: '一句话生成链上执行计划（MVP Demo）', gen: '生成计划', sample: '换个示例',
    intent: '意图解析', risk: '风控检查', status: '执行状态', plan: '执行步骤',
    confirm: '确认执行', reset: '重置', waiting: '⏳ 等待生成计划', planned: '✅ 计划已生成，待确认',
    executing: '🚀 执行中...', done: '🎉 执行完成（演示模式）',
    scenario: '场景', scenario_auto: '自动识别', scenario_trading: '交易版', scenario_operations: '运营版', scenario_payment: '支付版',
    note: 'Web demo only. 接入 OnchainOS API 后可执行真实链上动作。'
  },
  en: {
    subtitle: 'One-line intent to onchain execution plan (MVP Demo)', gen: 'Generate Plan', sample: 'Try Sample',
    intent: 'Intent', risk: 'Risk Checks', status: 'Execution Status', plan: 'Execution Steps',
    confirm: 'Confirm Execute', reset: 'Reset', waiting: '⏳ Waiting for plan', planned: '✅ Plan ready, waiting for confirmation',
    executing: '🚀 Executing...', done: '🎉 Execution completed (demo mode)',
    scenario: 'Scenario', scenario_auto: 'Auto detect', scenario_trading: 'Trading', scenario_operations: 'Operations', scenario_payment: 'Payments',
    note: 'Web demo only. Connect OnchainOS APIs for real execution.'
  }
};

let lang = 'zh';
let currentPlan = null;

const topicsPool = [
  'EigenLayer TVL 再创高',
  'Solana memecoin 热度',
  'Layer2 降费提案',
  'Bitcoin Runes 交易量',
  'Base 链用户数',
  'Modular 赛道融资',
];

function t(k){ return i18n[lang][k] || k; }

function applyI18n(){
  document.querySelectorAll('[data-i18n]').forEach(n => {
    n.textContent = t(n.dataset.i18n);
  });
  el('lang').textContent = lang === 'zh' ? 'EN' : '中';
  if (!currentPlan) el('status').textContent = t('waiting');
}

function detectScenario(text){
  const lower = text.toLowerCase();
  if (/(打|转|gas|address|transfer|send)/.test(text) || /0x[a-f0-9]{6}/i.test(text)) return 'payment';
  if (/(热点|内容|tweet|运营|观察|post|thread)/.test(text)) return 'operations';
  return 'trading';
}

function parseTradingIntent(text){
  const lower = text.toLowerCase();
  const intent = { asset: 'ETH', side: lower.includes('卖') || lower.includes('sell') ? 'SELL' : 'BUY', budget_usdt: 1000, tranches: 3, interval_min: 30, max_slippage_pct: 0.8, max_drawdown_pct: 5 };
  if (lower.includes('btc')) intent.asset = 'BTC';
  if (lower.includes('sol')) intent.asset = 'SOL';
  const mBudget = lower.match(/(\d+(?:\.\d+)?)\s*(usdt|usd|u)/); if(mBudget) intent.budget_usdt = Number(mBudget[1]);
  const mTr = text.match(/(?:分|in\s*)(\d+)\s*(?:笔|parts?)/i); if(mTr) intent.tranches = Number(mTr[1]);
  const mInt = text.match(/(\d+)\s*(?:分钟|min)/i); if(mInt) intent.interval_min = Number(mInt[1]);
  const mSlip = text.match(/(?:滑点|slippage)[^\d]*(\d+(?:\.\d+)?)\s*%/i); if(mSlip) intent.max_slippage_pct = Number(mSlip[1]);
  const mDraw = text.match(/(?:回撤|止损|stop)[^\d]*(\d+(?:\.\d+)?)\s*%/i); if(mDraw) intent.max_drawdown_pct = Number(mDraw[1]);
  return intent;
}

function parseOperationsIntent(text){
  const intent = { topics: 3, channel: 'X', include_watchlist: /(交易|观察|watch)/i.test(text), cadence: /(每周|weekly)/i.test(text) ? '每周' : '每日' };
  if (/小红书/.test(text)) intent.channel = 'Xiaohongshu';
  const mTopics = text.match(/(\d+)\s*(?:个)?(?:热点|topic|条)/i); if (mTopics) intent.topics = Number(mTopics[1]);
  return intent;
}

function parsePaymentIntent(text){
  const lower = text.toLowerCase();
  const intent = { amount: 100, token: 'USDT', recipient: '0xABCD...1234', max_gas_usd: 8, priority: /(延后|delay)/.test(text) ? 'defer' : 'normal' };
  const amountMatch = lower.match(/(\d+(?:\.\d+)?)\s*(usdt|usd|usdc|eth)/); if(amountMatch) intent.amount = Number(amountMatch[1]);
  const tokenMatch = lower.match(/(usdt|usdc|eth|btc|sol|sui)/); if(tokenMatch) intent.token = tokenMatch[1].toUpperCase();
  const addrMatch = text.match(/0x[a-fA-F0-9]{6,}/); if(addrMatch) intent.recipient = addrMatch[0];
  const gasMatch = text.match(/gas[^\d]*(\d+(?:\.\d+)?)/i); if(gasMatch) intent.max_gas_usd = Number(gasMatch[1]);
  return intent;
}

function marketSnapshot(asset){
  const base = { ETH: 3420, BTC: 61200, SOL: 128, SUI: 1.6 };
  const price = base[asset] || 100;
  const change = asset === 'BTC' ? 1.2 : -0.6;
  return { price, change_24h_pct: change, vol_24h_musd: asset === 'SOL' ? 92 : 140, trend: change > 0 ? 'Bullish' : 'Sideways' };
}

function buildTradingPlan(intent){
  const per = +(intent.budget_usdt / intent.tranches).toFixed(2);
  const steps = [];
  for(let idx=0; idx<intent.tranches; idx++){
    const amount = idx === intent.tranches - 1 ? +(intent.budget_usdt - per*(intent.tranches-1)).toFixed(2) : per;
    steps.push({ id: idx+1, action: `${intent.side} ${intent.asset}`, amount_usdt: amount, delay_min: idx*intent.interval_min, checks: ['slippage','twap'] });
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
      { name: 'Gas', value: '< 5 USDT', status: 'OK' },
    ],
    follow_up: ['24h 复盘：成交均价 vs. 市场', '波动超阈值自动暂停'],
  };
}

function sampleTopics(count){
  const list = [...topicsPool];
  list.sort(()=>Math.random()-0.5);
  return list.slice(0,count);
}

function buildOperationsPlan(intent){
  const topics = sampleTopics(intent.topics);
  const watchlist = intent.include_watchlist ? ['ETH/BTC 相关性下降','SOL 200 美元关注回调','SUI 生态空投窗口'] : [];
  const steps = [
    { id: 1, action: '抓取热点', output: topics },
    { id: 2, action: `生成 ${intent.channel} 可发内容`, output: topics.map(t => `${t} · CTA + 观点`) }
  ];
  if (watchlist.length) steps.push({ id: steps.length+1, action: '交易观察', output: watchlist });
  return {
    scenario: 'operations',
    title: '运营热点工作流',
    summary: `热点 ${intent.topics} 个 · ${intent.channel} · ${intent.cadence}`,
    intent,
    steps,
    risk: [
      { name: '事实核验', value: 'AI 草稿需人工确认', status: 'Pending' },
      { name: '免责声明', value: '默认附带', status: 'Auto' },
    ],
    follow_up: [`${intent.cadence} 回顾互动数据`, '热点/内容/观察一体归档'],
  };
}

function buildPaymentPlan(intent){
  const quote = { gas_usd: 5.8, eta: '< 2 min' };
  const compliance = intent.recipient.toLowerCase().startsWith('0xdead') ? 'blocked' : 'clean';
  return {
    scenario: 'payment',
    title: '链上支付助手',
    summary: `向 ${intent.recipient.slice(0,10)}... 转 ${intent.amount} ${intent.token}`,
    intent,
    steps: [
      { id: 1, action: 'Quote', details: quote },
      { id: 2, action: 'Compliance', details: { status: compliance } },
      { id: 3, action: 'Sign & Broadcast', details: { priority: intent.priority, max_gas: intent.max_gas_usd } },
    ],
    risk: [
      { name: 'Gas cap', value: `${quote.gas_usd}/${intent.max_gas_usd} USDT`, status: quote.gas_usd <= intent.max_gas_usd ? 'OK' : 'Hold' },
      { name: 'Compliance', value: compliance, status: compliance === 'clean' ? 'OK' : 'Blocked' },
    ],
    follow_up: ['生成支付回执 + 自动记账'],
  };
}

function buildPlan(text, forcedScenario){
  const scenario = forcedScenario === 'auto' ? detectScenario(text) : forcedScenario;
  if (scenario === 'operations') return buildOperationsPlan(parseOperationsIntent(text));
  if (scenario === 'payment') return buildPaymentPlan(parsePaymentIntent(text));
  return buildTradingPlan(parseTradingIntent(text));
}

function formatValue(v){
  if (Array.isArray(v)) return v.join(', ');
  if (typeof v === 'object' && v !== null) return JSON.stringify(v);
  return v;
}

function kvHtml(obj){
  return Object.entries(obj).map(([k,v])=>`<div class="kv"><span>${k}</span><strong>${formatValue(v)}</strong></div>`).join('');
}

function render(plan){
  el('intent').innerHTML = kvHtml(plan.intent);
  el('risk').innerHTML = plan.risk.map(item => `<div class="kv"><span>${item.name}</span><strong>${item.value} (${item.status})</strong></div>`).join('');
  el('steps').innerHTML = plan.steps.map(s => {
    let meta = [];
    if (s.amount_usdt) meta.push(`${s.amount_usdt} USDT`);
    if (typeof s.delay_min === 'number') meta.push(`T+${s.delay_min}m`);
    if (s.output) meta.push(s.output.join('<br/>'));
    if (s.details) meta.push(Object.entries(s.details).map(([k,v])=>`${k}: ${v}`).join(', '));
    if (s.checks) meta.push(`检查: ${s.checks.join(', ')}`);
    return `<div class="step" data-step="${s.id}"><div><span class="tag">#${s.id}</span> ${s.action}</div><div>${meta.join(' | ')}</div></div>`;
  }).join('');
  const statusLines = [plan.title, plan.summary];
  if (plan.market) statusLines.push(`行情：${plan.market.price} (${plan.market.change_24h_pct}% / ${plan.market.trend})`);
  if (plan.follow_up?.length) statusLines.push(`后续：${plan.follow_up.join('，')}`);
  statusLines.push(t('note'));
  el('status').innerHTML = statusLines.join('<br/>');
  el('output').textContent = JSON.stringify(plan, null, 2);
}

function generate(){
  const scenario = el('scenario').value;
  currentPlan = buildPlan(el('prompt').value.trim(), scenario);
  render(currentPlan);
  el('status').innerHTML += `<br/>${t('planned')}`;
  el('confirm').disabled = false;
}

async function runDemoExecution(){
  if(!currentPlan) return;
  el('status').textContent = t('executing');
  el('confirm').disabled = true;
  for (const step of currentPlan.steps){
    await new Promise(r=>setTimeout(r, 400));
    step.done = true;
    el('steps').querySelector(`[data-step="${step.id}"]`).classList.add('done');
  }
  el('status').textContent = t('done');
}

function resetAll(){
  currentPlan = null;
  el('intent').innerHTML = '';
  el('risk').innerHTML = '';
  el('steps').innerHTML = '';
  el('output').textContent = '点击“生成计划”...';
  el('status').textContent = t('waiting');
  el('confirm').disabled = true;
}

el('gen').addEventListener('click', generate);
el('sample').addEventListener('click', ()=>{
  const scenario = el('scenario').value === 'auto' ? detectScenario(el('prompt').value) : el('scenario').value;
  el('prompt').value = samples[scenario] || samples.trading;
});
el('confirm').addEventListener('click', runDemoExecution);
el('reset').addEventListener('click', resetAll);
el('lang').addEventListener('click', ()=>{ lang = lang === 'zh' ? 'en' : 'zh'; applyI18n(); if (currentPlan) render(currentPlan); });
el('scenario').addEventListener('change', ()=>{
  const val = el('scenario').value;
  if (val !== 'auto') el('prompt').value = samples[val];
});

applyI18n();
