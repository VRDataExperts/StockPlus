import { sb, fmtPct, cls } from './config.js';

let all = [], sort = { k: 'score', dir: -1 };

document.getElementById('refresh').onclick = () => load();
document.getElementById('f-strategy').onchange = render;
document.getElementById('f-fresh').onchange = render;
document.querySelectorAll('#op-table th').forEach(th => th.onclick = () => {
  const k = th.dataset.k;
  sort = { k, dir: sort.k === k ? -sort.dir : -1 };
  render();
});

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
  let rows = all.filter(r => (!s || r.strategy === s) && (!freshOnly || r.fresh));
  rows.sort((a, b) => (a[sort.k] > b[sort.k] ? 1 : -1) * sort.dir);
  document.getElementById('op-empty').classList.toggle('hidden', rows.length > 0);
  document.getElementById('op-body').innerHTML = rows.map(r => `
    <tr>
      <td>${r.ticker}</td>
      <td>${r.strategy}</td>
      <td>${r.fresh ? '🟢 buy' : 'hold-long'}</td>
      <td class="${cls(r.score)}">${fmtPct(r.score)}</td>
      <td>$${r.last_price ?? '—'}</td>
    </tr>`).join('');
}

load();
