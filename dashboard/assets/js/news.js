import { sb } from './config.js';

document.getElementById('refresh').onclick = () => load();

async function load() {
  const { data, error } = await sb.from('news_items')
    .select('*').order('published_at', { ascending: false }).limit(80);
  if (error) { console.error(error); return; }
  document.getElementById('news-empty').classList.toggle('hidden', (data || []).length > 0);
  document.getElementById('news-list').innerHTML = (data || []).map(n => `
    <div class="news-item">
      <a href="${n.url || '#'}" target="_blank" rel="noopener">${n.headline}</a>
      <div class="news-meta">
        ${(n.tickers || []).map(t => `<span class="tag">${t}</span>`).join('')}
        ${n.provider} · ${n.published_at ? new Date(n.published_at).toLocaleString() : ''}
      </div>
    </div>`).join('');
}

load();
