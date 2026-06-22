import { sb, fmtPct, cls } from './config.js';
import { openTickerModal } from './modal.js';

let all = [], view = [], sort = { k: 'confidence', dir: -1 };

document.getElementById('refresh').onclick = () => load();
['f-hz', 'f-strategy', 'f-conf', 'f-fresh'].forEach(id =>
  document.getElementById(id).addEventListener('change', render));
document.querySelectorAll('#mv-table th').forEach(th => th.onclick = () => {
  const k = th.dataset.k;
  sort = { k, dir: sort.k === k ? -sort.dir : -1 };
  render();
});

function confCell(c) {
  if (c == null) return '—';
  const color = c >= 70 ? 'var(--green)' : c < 50 ? 'var(--red)' : 'var(--muted)';
  return `<strong style="color:${color}">${Math.round(c)}</strong>`;
}
function moodCell(s) {
  if (s == null) return '—';
  const e = s > 0.1 ? '🟢' : s < -0.1 ? '🔴' : '⚪';
  return `${e} ${s.toFixed(2)}`;
}

async function load() {
  const { data, error } = await sb.from('movers')
    .select('*').order('confidence', { ascending: false }).limit(600);
  if (error) { console.error(error); return; }
  all = data || [];
  const strat = [...new Set(all.map(r => r.strategy))];
  document.getElementById('f-strategy').innerHTML =
    '<option value="">All</option>' + strat.map(s => `<option>${s}</option>`).join('');
  if (all[0]) document.getElementById('run-info').textContent =
    'Last scan: ' + new Date(all[0].run_at).toLocaleString();
  render();
}

function render() {
  const hz = document.getElementById('f-hz').value;
  const s = document.getElementById('f-strategy').value;
  const minC = +document.getElementById('f-conf').value;
  const freshOnly = document.getElementById('f-fresh').checked;
  view = all.filter(r =>
    (!hz || r.horizon === hz) && (!s || r.strategy === s) &&
    (r.confidence ?? 0) >= minC && (!freshOnly || r.fresh));
  view.sort((a, b) => ((a[sort.k] ?? -1) > (b[sort.k] ?? -1) ? 1 : -1) * sort.dir);
  document.getElementById('mv-empty').classList.toggle('hidden', view.length > 0);
  document.getElementById('mv-body').innerHTML = view.map((r, i) => `
    <tr data-i="${i}">
      <td>${r.ticker}</td><td>${r.horizon}</td><td>${r.strategy}</td>
      <td>${r.fresh ? '🟢 buy' : 'hold-long'}</td>
      <td>${confCell(r.confidence)}</td>
      <td>${r.volatility != null ? r.volatility + '%' : '—'}</td>
      <td class="${cls(r.momentum)}">${fmtPct(r.momentum)}</td>
      <td>${moodCell(r.sentiment)}</td>
      <td>$${r.last_price ?? '—'}</td>
    </tr>`).join('');
  document.querySelectorAll('#mv-body tr').forEach(tr => tr.onclick = () => {
    const r = view[+tr.dataset.i];
    openTickerModal(r.ticker, { strategy: r.strategy, signal: r.signal, score: r.momentum, sentiment: r.sentiment, confidence: r.confidence, volatility: r.volatility, horizon: r.horizon });
  });
}

load();
