import { sb, fmtPct, fmtNum, cls } from './config.js';

async function load() {
  const { data: rows, error } = await sb.from('backtests').select('*').limit(2000);
  if (error) { console.error(error); return; }

  // newest per (strategy,ticker,period)
  const seen = new Set(), latest = [];
  for (const r of [...rows].sort((a, b) => (a.run_at < b.run_at ? 1 : -1))) {
    const k = r.strategy + '|' + r.ticker + '|' + r.period_label;
    if (!seen.has(k)) { seen.add(k); latest.push(r); }
  }

  const { count: newsCount } = await sb
    .from('news_items').select('*', { count: 'exact', head: true });

  const tickers = new Set(latest.map(r => r.ticker));
  const strategies = [...new Set(latest.map(r => r.strategy))];

  document.getElementById('cards').innerHTML = `
    ${card('Backtests', latest.length)}
    ${card('Tickers', tickers.size)}
    ${card('Strategies', strategies.length)}
    ${card('News stored', newsCount ?? '—')}`;

  // leaderboard: averages per strategy
  const board = strategies.map(s => {
    const g = latest.filter(r => r.strategy === s);
    const avg = k => g.reduce((a, r) => a + (r[k] || 0), 0) / g.length;
    return { s, n: g.length, ret: avg('total_return'), sharpe: avg('sharpe'), dd: avg('max_drawdown') };
  }).sort((a, b) => b.sharpe - a.sharpe);

  document.getElementById('board').innerHTML = board.map(b => `
    <tr>
      <td>${b.s}</td>
      <td class="${cls(b.ret)}">${fmtPct(b.ret)}</td>
      <td>${fmtNum(b.sharpe)}</td>
      <td class="neg">${fmtPct(b.dd)}</td>
      <td>${b.n}</td>
    </tr>`).join('');
}

const card = (label, value) =>
  `<div class="card"><div class="label">${label}</div><div class="value">${value}</div></div>`;

document.getElementById('refresh').onclick = () => location.reload();
load();
