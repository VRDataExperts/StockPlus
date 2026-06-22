import { sb } from './config.js';

let chart = null;

function ensure() {
  if (document.getElementById('modal-backdrop')) return;
  const d = document.createElement('div');
  d.id = 'modal-backdrop'; d.className = 'modal-backdrop hidden';
  d.innerHTML = `<div class="modal" role="dialog" aria-modal="true">
    <button class="modal-close" aria-label="Close">×</button>
    <h3 id="m-title"></h3>
    <div id="m-sub" class="sub" style="color:var(--muted)"></div>
    <canvas id="m-chart" height="120" style="margin-top:10px"></canvas>
    <div id="m-nochart" class="empty hidden" style="padding:18px">Price chart not generated for this ticker yet — it appears after the next data refresh (charts.py).</div>
    <div id="m-explain" class="explain"></div>
    <div id="m-fund" class="cards"></div>
  </div>`;
  document.body.appendChild(d);
  d.addEventListener('click', e => { if (e.target === d) close(); });
  d.querySelector('.modal-close').onclick = close;
  document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
}
function close() {
  const d = document.getElementById('modal-backdrop');
  if (d) d.classList.add('hidden');
  if (chart) { chart.destroy(); chart = null; }
}

export async function openTickerModal(ticker, ctx = {}) {
  ensure();
  document.getElementById('modal-backdrop').classList.remove('hidden');
  document.getElementById('m-title').textContent = ticker;
  document.getElementById('m-sub').textContent = 'Loading…';

  const [cdRes, fRes] = await Promise.all([
    sb.from('chart_data').select('*').eq('ticker', ticker).single(),
    sb.from('fundamentals').select('*').eq('ticker', ticker).single(),
  ]);
  const cd = cdRes.data, f = fRes.data;
  document.getElementById('m-sub').textContent = f?.name ? `${f.name}${f.sector ? ' · ' + f.sector : ''}` : '';

  const canvas = document.getElementById('m-chart');
  const noChart = document.getElementById('m-nochart');
  if (cd) {
    canvas.style.display = ''; noChart.classList.add('hidden');
    const pts = cd.points, labels = pts.map(p => p.t);
    const idx = Object.fromEntries(labels.map((l, i) => [l, i]));
    const buy = Array(labels.length).fill(null), sell = Array(labels.length).fill(null);
    for (const m of (cd.markers || [])) {
      if (ctx.strategy && m.strategy !== ctx.strategy) continue;
      if (m.t in idx) (m.side === 'buy' ? buy : sell)[idx[m.t]] = m.price;
    }
    if (chart) chart.destroy();
    chart = new Chart(canvas, {
      type: 'line',
      data: { labels, datasets: [
        { label: 'Close', data: pts.map(p => p.close), borderColor: '#e6edf3', borderWidth: 1.6, pointRadius: 0, tension: .1 },
        { label: 'SMA20', data: pts.map(p => p.sma20), borderColor: '#58a6ff', borderWidth: 1, pointRadius: 0, tension: .1 },
        { label: 'SMA50', data: pts.map(p => p.sma50), borderColor: '#d29922', borderWidth: 1, pointRadius: 0, tension: .1 },
        { label: 'Buy', data: buy, borderColor: '#3fb950', backgroundColor: '#3fb950', showLine: false, pointStyle: 'triangle', pointRadius: 7 },
        { label: 'Sell', data: sell, borderColor: '#f85149', backgroundColor: '#f85149', showLine: false, pointStyle: 'triangle', rotation: 180, pointRadius: 7 },
      ]},
      options: { responsive: true, plugins: { legend: { labels: { color: '#e6edf3', boxWidth: 12 } } },
        scales: { x: { ticks: { color: '#8b949e', maxTicksLimit: 7 }, grid: { color: '#21262d' } },
                  y: { ticks: { color: '#8b949e' }, grid: { color: '#21262d' } } } }
    });
  } else {
    if (chart) { chart.destroy(); chart = null; }
    canvas.style.display = 'none'; noChart.classList.remove('hidden');
  }

  document.getElementById('m-explain').innerHTML = explain(ticker, ctx, f);
  const pct = v => v == null ? '—' : (v * 100).toFixed(1) + '%';
  const card = (l, v) => `<div class="card"><div class="label">${l}</div><div class="value">${v}</div></div>`;
  document.getElementById('m-fund').innerHTML = f ?
    card('Strength', f.strength_score != null ? Math.round(f.strength_score) + '/100' : '—') +
    card('Profit margin', pct(f.profit_margin)) + card('ROE', pct(f.roe)) +
    card('Rev growth', pct(f.revenue_growth)) + card('P/E', f.pe != null ? Number(f.pe).toFixed(1) : '—') : '';
}

function explain(ticker, ctx, f) {
  const fam = {
    breakout: 'trend-following — buys new highs, exits on weakness',
    momentum: 'trend-following — rides established uptrends',
    macd: 'trend/momentum — acts when momentum turns up',
    mean_reversion: 'mean-reversion — buys dips, sells into recovery',
    bollinger: 'mean-reversion — buys when statistically cheap',
  }[ctx.strategy] || 'a trading rule';
  const isTrend = /breakout|momentum|macd/.test(ctx.strategy || '');
  const mom = ctx.score != null ? (ctx.score * 100).toFixed(1) + '%' : 'n/a';
  const strength = ctx.strength_score ?? f?.strength_score;
  const strong = strength != null && strength >= 65;
  const fresh = ctx.signal === 'buy';

  // why-now: what specifically triggered
  const trigger = {
    breakout: 'price just closed above its recent high (a breakout)',
    momentum: 'the short-term average just crossed above the long-term one',
    macd: 'the MACD line just crossed above its signal line',
    mean_reversion: 'RSI just dropped into oversold territory',
    bollinger: 'price just closed below the lower Bollinger band',
  }[ctx.strategy] || 'the rule just turned positive';

  const horizonLine = ctx.horizon
    ? ` Tuned to the <strong>${ctx.horizon}</strong> horizon (${ctx.horizon === 'day' ? 'fastest settings, hold days' : ctx.horizon === 'week' ? 'medium settings, hold ~1–3 weeks' : 'slower settings, hold weeks–months'}).`
    : '';
  const confLine = ctx.confidence != null
    ? `<p><strong>Confidence:</strong> ${Math.round(ctx.confidence)}/100 — ${ctx.confidence >= 70 ? 'strong alignment of trend, momentum, volume and sentiment' : ctx.confidence >= 50 ? 'mixed signals' : 'weak — caution'}.</p>` : '';
  const volLine = ctx.volatility != null
    ? ` Volatility is ${ctx.volatility}% annualized (${ctx.volatility > 60 ? 'very high — swings hard' : ctx.volatility > 35 ? 'high' : 'moderate'}).` : '';

  let verdict;
  if (fresh && strong && ctx.score > 0) verdict = 'Higher-conviction — a fresh buy on a financially strong company with positive momentum.';
  else if (fresh && strong) verdict = 'Worth a look — fresh buy on a strong company, though momentum is soft.';
  else if (fresh) verdict = 'Speculative — fresh buy signal, but the company score is modest or volatility is high. Be cautious.';
  else verdict = 'Already trending — the rule is holding long; no new entry today.';

  return `
    <p><strong>What this is:</strong> the <em>${ctx.strategy || 'strategy'}</em> rule (${fam}) signals
      <strong>${fresh ? 'a fresh BUY' : 'HOLD (already long)'}</strong> on ${ticker}.${horizonLine}</p>
    <p><strong>Why now:</strong> ${fresh ? 'it was flagged today because ' + trigger + '.' : 'no new entry today — it has been long and the trend is still intact.'}</p>
    <p><strong>The numbers, plainly:</strong> price is ${ctx.score > 0 ? 'up' : 'down'} ${mom} over the last month.
      Company strength is ${strength != null ? Math.round(strength) + '/100' : 'unknown'} ${strong ? '(financially solid)' : '(mixed/weak or not rated)'}.${volLine}</p>
    ${confLine}
    <p><strong>Is this an opportunity?</strong> ${verdict}</p>
    <p><strong>What to expect:</strong> ${isTrend
      ? 'trend rules aim to ride further gains but exit if the trend breaks'
      : 'mean-reversion aims for a bounce toward the average and exits on recovery'}.
      Green triangles on the chart are past buys, red are sells. This is a research signal,
      <strong>not advice</strong> — many signals fail, so size small and set your exit first.</p>`;
}
