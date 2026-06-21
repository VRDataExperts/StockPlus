import { sb, fmtPct, cls } from './config.js';

let allRows = [], sort = { k: 'total_return', dir: -1 }, chart = null;

document.getElementById('refresh').onclick = () => load();
document.getElementById('period').onchange = render;
document.getElementById('ticker').onchange = render;
document.querySelectorAll('#bt-table th').forEach(th => th.onclick = () => {
  const k = th.dataset.k;
  sort = { k, dir: sort.k === k ? -sort.dir : -1 };
  render();
});

async function load() {
  const { data, error } = await sb.from('backtests')
    .select('*').order('run_at', { ascending: false }).limit(2000);
  if (error) { console.error(error); return; }
  const seen = new Set(); allRows = [];
  for (const r of data) {
    const k = r.strategy + '|' + r.ticker + '|' + r.period_label;
    if (!seen.has(k)) { seen.add(k); allRows.push(r); }
  }
  fill('period', [...new Set(allRows.map(r => r.period_label))]);
  fill('ticker', [...new Set(allRows.map(r => r.ticker))]);
  render();
}

function fill(id, vals) {
  const el = document.getElementById(id), cur = el.value;
  el.innerHTML = '<option value="">All</option>' + vals.map(v => `<option>${v}</option>`).join('');
  if ([...el.options].some(o => o.value === cur)) el.value = cur;
}

function render() {
  const p = document.getElementById('period').value;
  const t = document.getElementById('ticker').value;
  let rows = allRows.filter(r => (!p || r.period_label === p) && (!t || r.ticker === t));
  rows.sort((a, b) => (a[sort.k] > b[sort.k] ? 1 : -1) * sort.dir);
  document.getElementById('bt-empty').classList.toggle('hidden', rows.length > 0);
  const body = document.getElementById('bt-body');
  body.innerHTML = rows.map(r => `
    <tr data-id="${r.id}">
      <td>${r.ticker}</td><td>${r.strategy}</td>
      <td class="${cls(r.total_return)}">${fmtPct(r.total_return)}</td>
      <td>${fmtPct(r.bh_total_return)}</td>
      <td class="neg">${fmtPct(r.max_drawdown)}</td>
      <td>${r.sharpe == null ? '—' : r.sharpe.toFixed(2)}</td>
      <td>${r.trades ?? '—'}</td>
      <td>${fmtPct(r.time_in_market)}</td>
    </tr>`).join('');
  body.querySelectorAll('tr').forEach(tr => tr.onclick = () => {
    body.querySelectorAll('tr').forEach(x => x.classList.remove('sel'));
    tr.classList.add('sel');
    loadCurve(+tr.dataset.id, rows.find(r => r.id == tr.dataset.id));
  });
}

async function loadCurve(id, row) {
  const { data, error } = await sb.from('backtest_curves')
    .select('points').eq('backtest_id', id).single();
  if (error || !data) { console.error(error); return; }
  const pts = data.points;
  document.getElementById('chart-title').textContent =
    `${row.ticker} · ${row.strategy} · ${row.period_label} — strategy vs buy & hold (growth of $1)`;
  if (chart) chart.destroy();
  chart = new Chart(document.getElementById('curve'), {
    type: 'line',
    data: {
      labels: pts.map(p => p.t),
      datasets: [
        { label: 'Strategy', data: pts.map(p => p.strat), borderColor: '#58a6ff', borderWidth: 2, pointRadius: 0, tension: .1 },
        { label: 'Buy & Hold', data: pts.map(p => p.bh), borderColor: '#8b949e', borderWidth: 1.5, borderDash: [5, 4], pointRadius: 0, tension: .1 },
      ]
    },
    options: {
      responsive: true, plugins: { legend: { labels: { color: '#e6edf3' } } },
      scales: {
        x: { ticks: { color: '#8b949e', maxTicksLimit: 8 }, grid: { color: '#21262d' } },
        y: { ticks: { color: '#8b949e' }, grid: { color: '#21262d' } }
      }
    }
  });
}

load();
