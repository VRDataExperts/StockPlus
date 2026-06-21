import { sb, fmtPct, fmtNum, cls } from './config.js';

const card = (label, value) =>
  `<div class="card"><div class="label">${label}</div><div class="value">${value}</div></div>`;

async function loadLive() {
  const { data, error } = await sb.from('live_quotes').select('*').order('ticker');
  if (error) { return; }
  const rows = data || [];
  if (!rows.length) { document.getElementById('live-head').style.display = 'none'; return; }
  const newest = rows.reduce((a, r) => r.updated_at > a ? r.updated_at : a, '');
  document.getElementById('live-head').innerHTML =
    `<span class="live-dot">●</span> LIVE PRICES — updated ${new Date(newest).toLocaleTimeString()}`;
  document.getElementById('live').innerHTML = rows.map(r => {
    const c = r.change_pct > 0 ? 'pos' : r.change_pct < 0 ? 'neg' : '';
    const arrow = r.change_pct > 0 ? '▲' : r.change_pct < 0 ? '▼' : '·';
    return `<div class="quote"><div class="t">${r.ticker}</div>
      <div class="p">$${r.price ?? '—'}</div>
      <div class="c ${c}">${arrow} ${r.change_pct == null ? '—' : r.change_pct.toFixed(2) + '%'}</div></div>`;
  }).join('');
}

async function loadBoard() {
  const { data: rows, error } = await sb.from('backtests').select('*').limit(2000);
  if (error) { console.error(error); return; }
  const seen = new Set(), latest = [];
  for (const r of [...rows].sort((a, b) => (a.run_at < b.run_at ? 1 : -1))) {
    const k = r.strategy + '|' + r.ticker + '|' + r.period_label;
    if (!seen.has(k)) { seen.add(k); latest.push(r); }
  }
  const { count: newsCount } = await sb.from('news_items').select('*', { count: 'exact', head: true });
  const tickers = new Set(latest.map(r => r.ticker));
  const strategies = [...new Set(latest.map(r => r.strategy))];
  document.getElementById('cards').innerHTML =
    card('Backtests', latest.length) + card('Tickers', tickers.size) +
    card('Strategies', strategies.length) + card('News stored', newsCount ?? '—');
  const board = strategies.map(s => {
    const g = latest.filter(r => r.strategy === s);
    const avg = k => g.reduce((a, r) => a + (r[k] || 0), 0) / g.length;
    return { s, n: g.length, ret: avg('total_return'), sharpe: avg('sharpe'), dd: avg('max_drawdown') };
  }).sort((a, b) => b.sharpe - a.sharpe);
  document.getElementById('board').innerHTML = board.map(b => `
    <tr><td>${b.s}</td><td class="${cls(b.ret)}">${fmtPct(b.ret)}</td>
      <td>${fmtNum(b.sharpe)}</td><td class="neg">${fmtPct(b.dd)}</td><td>${b.n}</td></tr>`).join('');
}

document.getElementById('refresh').onclick = () => { loadLive(); loadBoard(); };
loadLive(); loadBoard();
setInterval(loadLive, 30000);   // refresh live prices every 30s
