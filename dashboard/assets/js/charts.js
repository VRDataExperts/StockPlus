import { sb } from './config.js';

let cur = null, range = '1Y', chartMain = null, chartBig = null;
const DAYS = { '7D': 5, '15D': 10, '1M': 21, '3M': 63, '6M': 126, '1Y': 252, '2Y': 504, '5Y': 1260, '10Y': 2600, 'MAX': 999999 };

const optsBase = {
  responsive: true, interaction: { mode: 'index', intersect: false },
  plugins: { legend: { labels: { color: '#e6edf3', boxWidth: 12 } } },
  scales: { x: { ticks: { color: '#8b949e', maxTicksLimit: 8 }, grid: { color: '#21262d' } },
            y: { ticks: { color: '#8b949e' }, grid: { color: '#21262d' } } }
};

document.getElementById('refresh').onclick = () => init();
document.getElementById('ticker').onchange = () => loadTicker();
document.getElementById('mstrat').onchange = () => { renderMain(); if (bigOpen()) renderBig(); };
document.querySelectorAll('.range-btn').forEach(b => b.onclick = () => {
  range = b.dataset.r;
  document.querySelectorAll('.range-btn').forEach(x => x.classList.toggle('active', x === b));
  renderMain(); if (bigOpen()) renderBig();
});
document.getElementById('enlarge').onclick = () => openBig();
document.getElementById('big-close').onclick = closeBig;
document.getElementById('big-backdrop').addEventListener('click', e => { if (e.target.id === 'big-backdrop') closeBig(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeBig(); });

async function init() {
  const { data: list, error } = await sb.from('chart_data').select('ticker').order('ticker');
  if (error) { console.error(error); return; }
  const tickers = (list || []).map(r => r.ticker);
  document.getElementById('charts-empty').classList.toggle('hidden', tickers.length > 0);
  document.getElementById('ticker').innerHTML = tickers.map(t => `<option>${t}</option>`).join('');
  if (tickers.length) loadTicker();
}

async function loadTicker() {
  const ticker = document.getElementById('ticker').value;
  if (!ticker) return;
  const [{ data: row }, { data: f }] = await Promise.all([
    sb.from('chart_data').select('*').eq('ticker', ticker).single(),
    sb.from('fundamentals').select('*').eq('ticker', ticker).single(),
  ]);
  cur = { row, f };
  const strats = [...new Set((row?.markers || []).map(m => m.strategy))];
  const sel = document.getElementById('mstrat');
  if (sel.options.length <= 1)
    sel.innerHTML = '<option value="">All signals</option>' + strats.map(s => `<option>${s}</option>`).join('');
  document.getElementById('info').textContent = f?.name ? `${f.name}${f.sector ? ' · ' + f.sector : ''}` : '';
  renderMain(); renderFund();
}

const slice = pts => pts.slice(Math.max(0, pts.length - DAYS[range]));

function build(points, markers, mstrat) {
  const labels = points.map(p => p.t), idx = Object.fromEntries(labels.map((l, i) => [l, i]));
  const buy = Array(labels.length).fill(null), sell = Array(labels.length).fill(null);
  for (const m of (markers || [])) {
    if (mstrat && m.strategy !== mstrat) continue;
    if (m.t in idx) (m.side === 'buy' ? buy : sell)[idx[m.t]] = m.price;
  }
  const line = (label, key, color, bw, dash) =>
    ({ label, data: points.map(p => p[key]), borderColor: color, borderWidth: bw, borderDash: dash || [], pointRadius: 0, tension: .1 });
  return { labels, datasets: [
    line('Close', 'close', '#e6edf3', 1.8), line('SMA20', 'sma20', '#58a6ff', 1), line('SMA50', 'sma50', '#d29922', 1),
    line('BB upper', 'bb_up', '#3fb95066', 1, [4, 4]), line('BB lower', 'bb_lo', '#3fb95066', 1, [4, 4]),
    { label: 'Buy', data: buy, borderColor: '#3fb950', backgroundColor: '#3fb950', showLine: false, pointStyle: 'triangle', pointRadius: 7 },
    { label: 'Sell', data: sell, borderColor: '#f85149', backgroundColor: '#f85149', showLine: false, pointStyle: 'triangle', rotation: 180, pointRadius: 7 },
  ]};
}

function renderMain() {
  if (!cur?.row) return;
  const d = build(slice(cur.row.points), cur.row.markers, document.getElementById('mstrat').value);
  if (chartMain) chartMain.destroy();
  chartMain = new Chart(document.getElementById('px'), { type: 'line', data: d, options: optsBase });
}
function renderBig() {
  if (!cur?.row) return;
  const d = build(slice(cur.row.points), cur.row.markers, document.getElementById('mstrat').value);
  if (chartBig) chartBig.destroy();
  chartBig = new Chart(document.getElementById('px-big'),
    { type: 'line', data: d, options: { ...optsBase, maintainAspectRatio: false } });
}
function renderFund() {
  const f = cur?.f, el = document.getElementById('fund');
  if (!f) { el.innerHTML = ''; return; }
  const pct = v => v == null ? '—' : (v * 100).toFixed(1) + '%';
  const card = (l, v) => `<div class="card"><div class="label">${l}</div><div class="value">${v}</div></div>`;
  el.innerHTML = card('Strength', f.strength_score != null ? Math.round(f.strength_score) + '/100' : '—') +
    card('Profit margin', pct(f.profit_margin)) + card('ROE', pct(f.roe)) +
    card('Revenue growth', pct(f.revenue_growth)) + card('P/E', f.pe != null ? Number(f.pe).toFixed(1) : '—');
}

const bigOpen = () => !document.getElementById('big-backdrop').classList.contains('hidden');
function openBig() {
  if (!cur?.row) return;
  document.getElementById('big-title').textContent =
    document.getElementById('ticker').value + ' — ' + range;
  document.getElementById('big-backdrop').classList.remove('hidden');
  renderBig();
}
function closeBig() {
  document.getElementById('big-backdrop').classList.add('hidden');
  if (chartBig) { chartBig.destroy(); chartBig = null; }
}

init();
