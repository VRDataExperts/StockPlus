import { sb, fmtPct, cls } from './config.js';

let all = [], sort = { k: 'score', dir: -1 };

document.getElementById('refresh').onclick = () => load();
['f-strategy', 'f-fresh', 'f-strong'].forEach(id =>
  document.getElementById(id).addEventListener('change', render));
document.querySelectorAll('#op-table th').forEach(th => th.onclick = () => {
  const k = th.dataset.k;
  sort = { k, dir: sort.k === k ? -sort.dir : -1 };
  render();
});

function strengthCell(s) {
  if (s == null) return '—';
  const color = s >= 65 ? 'var(--green)' : s < 40 ? 'var(--red)' : 'var(--muted)';
  return `<span style="color:${color}">${Math.round(s)}</span>`;
}
function moodCell(s) {
  if (s == null) return '—';
  const e = s > 0.1 ? '🟢' : s < -0.1 ? '🔴' : '⚪';
  return `${e} ${s.toFixed(2)}`;
}

async function load() {
  const { data, error } = await sb.from('opportunities')
    .select('*').order('score', { ascending: false }).limit(500);
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
  const s = document.getElementById('f-strategy').value;
  const freshOnly = document.getElementById('f-fresh').checked;
  const strongOnly = document.getElementById('f-strong').checked;
  let rows = all.filter(r =>
    (!s || r.strategy === s) &&
    (!freshOnly || r.fresh) &&
    (!strongOnly || (r.strength_score != null && r.strength_score >= 65)));
  rows.sort((a, b) => ((a[sort.k] ?? -1) > (b[sort.k] ?? -1) ? 1 : -1) * sort.dir);
  document.getElementById('op-empty').classList.toggle('hidden', rows.length > 0);
  document.getElementById('op-body').innerHTML = rows.map(r => `
    <tr>
      <td>${r.ticker}</td>
      <td>${r.strategy}</td>
      <td>${r.fresh ? '🟢 buy' : 'hold-long'}</td>
      <td class="${cls(r.score)}">${fmtPct(r.score)}</td>
      <td>${strengthCell(r.strength_score)}</td>
      <td>${moodCell(r.sentiment)}</td>
      <td>$${r.last_price ?? '—'}</td>
    </tr>`).join('');
}

load();
