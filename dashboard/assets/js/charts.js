import { sb, fmtPct } from './config.js';

let data = null, chart = null;

document.getElementById('refresh').onclick = () => init();
document.getElementById('ticker').onchange = () => draw();
document.getElementById('mstrat').onchange = () => draw();

async function init() {
  const { data: list, error } = await sb.from('chart_data').select('ticker').order('ticker');
  if (error) { console.error(error); return; }
  const tickers = (list || []).map(r => r.ticker);
  document.getElementById('charts-empty').classList.toggle('hidden', tickers.length > 0);
  document.getElementById('ticker').innerHTML = tickers.map(t => `<option>${t}</option>`).join('');
  if (tickers.length) draw();
}

async function draw() {
  const ticker = document.getElementById('ticker').value;
  if (!ticker) return;
  const { data: row } = await sb.from('chart_data').select('*').eq('ticker', ticker).single();
  if (!row) return;
  data = row;

  // strategy filter for markers
  const strats = [...new Set((row.markers || []).map(m => m.strategy))];
  const sel = document.getElementById('mstrat');
  if (sel.options.length === 0 || ![...sel.options].some(o => strats.includes(o.value)))
    sel.innerHTML = '<option value="">All signals</option>' + strats.map(s => `<option>${s}</option>`).join('');
  const mstrat = sel.value;

  const pts = row.points;
  const labels = pts.map(p => p.t);
  const idx = Object.fromEntries(labels.map((l, i) => [l, i]));
  const buy = Array(labels.length).fill(null), sell = Array(labels.length).fill(null);
  for (const m of (row.markers || [])) {
    if (mstrat && m.strategy !== mstrat) continue;
    if (m.t in idx) (m.side === 'buy' ? buy : sell)[idx[m.t]] = m.price;
  }

  const line = (label, key, color, dash) => ({
    label, data: pts.map(p => p[key]), borderColor: color, borderWidth: dash ? 1 : 1.8,
    borderDash: dash || [], pointRadius: 0, tension: .1,
  });
  if (chart) chart.destroy();
  chart = new Chart(document.getElementById('px'), {
    type: 'line',
    data: { labels, datasets: [
      line('Close', 'close', '#e6edf3'),
      line('SMA20', 'sma20', '#58a6ff'),
      line('SMA50', 'sma50', '#d29922'),
      line('BB upper', 'bb_up', '#3fb95066', [4, 4]),
      line('BB lower', 'bb_lo', '#3fb95066', [4, 4]),
      { label: 'Buy', data: buy, borderColor: '#3fb950', backgroundColor: '#3fb950',
        showLine: false, pointStyle: 'triangle', pointRadius: 7 },
      { label: 'Sell', data: sell, borderColor: '#f85149', backgroundColor: '#f85149',
        showLine: false, pointStyle: 'triangle', rotation: 180, pointRadius: 7 },
    ]},
    options: { responsive: true, interaction: { mode: 'index', intersect: false },
      plugins: { legend: { labels: { color: '#e6edf3', boxWidth: 12 } } },
      scales: { x: { ticks: { color: '#8b949e', maxTicksLimit: 8 }, grid: { color: '#21262d' } },
                y: { ticks: { color: '#8b949e' }, grid: { color: '#21262d' } } } }
  });

  drawFundamentals(ticker);
}

async function drawFundamentals(ticker) {
  const { data: f } = await sb.from('fundamentals').select('*').eq('ticker', ticker).single();
  const el = document.getElementById('fund');
  if (!f) { el.innerHTML = ''; return; }
  const card = (label, val) =>
    `<div class="card"><div class="label">${label}</div><div class="value">${val}</div></div>`;
  const pct = v => v == null ? '—' : (v * 100).toFixed(1) + '%';
  document.getElementById('info').textContent =
    `${f.name || ticker}${f.sector ? ' · ' + f.sector : ''}`;
  el.innerHTML =
    card('Strength', f.strength_score != null ? Math.round(f.strength_score) + '/100' : '—') +
    card('Profit margin', pct(f.profit_margin)) +
    card('ROE', pct(f.roe)) +
    card('Revenue growth', pct(f.revenue_growth)) +
    card('P/E', f.pe != null ? Number(f.pe).toFixed(1) : '—');
}

init();
