const state = { interests: [] };
const $ = (id) => document.getElementById(id);

function slugify(text) {
  return text.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || crypto.randomUUID();
}

function parseList(value) {
  return value.split(',').map(s => s.trim()).filter(Boolean);
}

function showToast(message = 'Saved locally ✓') {
  const toast = $('toast');
  toast.textContent = message;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 1200);
}

async function loadInterests() {
  const response = await fetch('/api/interests');
  const payload = await response.json();
  state.interests = payload.interests || [];
  render();
}

async function saveInterests() {
  const response = await fetch('/api/interests', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ interests: state.interests }, null, 2),
  });
  if (!response.ok) throw new Error(await response.text());
  $('saveButton').textContent = 'Saved ✓';
  showToast();
  setTimeout(() => $('saveButton').textContent = 'Save now', 1200);
}

async function checkTechnologyUpdates() {
  const button = $('checkUpdatesButton');
  const panel = $('updatesPanel');
  button.textContent = 'Checking…';
  button.disabled = true;
  try {
    const response = await fetch('/api/technology-updates');
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || 'Failed to fetch updates');
    renderTechnologyUpdates(payload);
    showToast('Technology updates checked ✓');
  } catch (error) {
    panel.hidden = false;
    panel.innerHTML = `<p class="updates-error">${escapeHtml(error.message)}</p>`;
  } finally {
    button.textContent = 'Check technology updates';
    button.disabled = false;
  }
}

function renderTechnologyUpdates(payload) {
  const panel = $('updatesPanel');
  panel.hidden = false;
  const updates = payload.updates || [];
  const errors = payload.errors || [];
  const checked = payload.interests_checked || 0;
  const updateMarkup = updates.length
    ? updates.slice(0, 8).map(update => `
        <article class="update-item">
          <strong>${escapeHtml(update.interest_name)}</strong>
          <a href="${escapeHtml(update.url)}" target="_blank" rel="noreferrer">${escapeHtml(update.title || 'Untitled update')}</a>
          ${update.published ? `<span>${escapeHtml(update.published)}</span>` : ''}
        </article>
      `).join('')
    : '<p>No matching technology updates found yet.</p>';
  const errorMarkup = errors.length
    ? `<p class="updates-error">${errors.length} feed error${errors.length === 1 ? '' : 's'} while checking updates.</p>`
    : '';
  panel.innerHTML = `
    <h3>Technology updates</h3>
    <p>${checked} technology feed${checked === 1 ? '' : 's'} checked</p>
    ${updateMarkup}
    ${errorMarkup}
  `;
}

function addInterest(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const name = $('name').value.trim();
  if (!name) return;

  state.interests.unshift({
    id: `${slugify(name)}-${Date.now()}`,
    name,
    type: 'technology',
    priority: $('priority').value,
    official_site_url: $('officialSiteUrl').value.trim(),
    official_feed_url: $('officialFeedUrl').value.trim(),
    watch_keywords: parseList($('watchKeywords').value),
    ignore_keywords: parseList($('ignoreKeywords').value),
    notes: $('notes').value.trim(),
    enabled: true,
  });
  form.reset();
  $('priority').value = 'medium';
  render();
  saveInterests().catch(alert);
}

function toggleInterest(id) {
  const interest = state.interests.find(item => item.id === id);
  if (interest) interest.enabled = !interest.enabled;
  render();
  saveInterests().catch(alert);
}

function deleteInterest(id) {
  state.interests = state.interests.filter(item => item.id !== id);
  render();
  saveInterests().catch(alert);
}

function renderStats() {
  const enabled = state.interests.filter(item => item.enabled).length;
  const feeds = state.interests.filter(item => item.type === 'technology' && item.official_feed_url).length;
  $('enabledCount').textContent = enabled;
  $('totalCount').textContent = state.interests.length;
  $('sourceCount').textContent = feeds;
}

function render() {
  renderStats();
  const cards = $('cards');
  cards.innerHTML = '';

  if (!state.interests.length) {
    cards.innerHTML = '<p class="empty">No interests yet. Add one on the left and the engine wakes up. Tiny robot noises optional.</p>';
    return;
  }

  for (const item of state.interests) {
    const card = document.createElement('article');
    card.className = `card ${item.enabled ? '' : 'disabled'}`;

    card.innerHTML = `
      <div class="card-main">
        <div>
          <h3>${escapeHtml(item.name)}</h3>
          <div class="meta">
            <span class="badge">${escapeHtml(item.type)}</span>
            <span class="badge priority-${escapeHtml(item.priority)}">${escapeHtml(item.priority)}</span>
            <span class="badge">${item.enabled ? 'enabled' : 'paused'}</span>
          </div>
        </div>
        <p>${escapeHtml(item.notes || 'No notes yet. Add what good signal looks like for this topic.')}</p>
        ${renderOfficialLinks(item)}
      </div>
      <div class="actions">
        <button class="button ghost" data-action="toggle" data-id="${item.id}">${item.enabled ? 'Disable' : 'Enable'}</button>
        <button class="button danger" data-action="delete" data-id="${item.id}">Delete</button>
      </div>
    `;
    cards.appendChild(card);
  }
}

function renderOfficialLinks(item) {
  if (item.type !== 'technology') return '';
  const links = [];
  if (item.official_site_url) links.push(`<a href="${escapeHtml(item.official_site_url)}" target="_blank" rel="noreferrer">official site</a>`);
  if (item.official_feed_url) links.push(`<a href="${escapeHtml(item.official_feed_url)}" target="_blank" rel="noreferrer">updates feed</a>`);
  const watch = (item.watch_keywords || []).map(keyword => `<span class="source">watch:${escapeHtml(keyword)}</span>`).join('');
  const ignore = (item.ignore_keywords || []).map(keyword => `<span class="source">ignore:${escapeHtml(keyword)}</span>`).join('');
  if (!links.length && !watch && !ignore) return '';
  return `<div class="official-links">${links.join('')}${watch}${ignore}</div>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[char]));
}

$('interestForm').addEventListener('submit', addInterest);
$('saveButton').addEventListener('click', () => saveInterests().catch(alert));
$('checkUpdatesButton').addEventListener('click', checkTechnologyUpdates);
$('cards').addEventListener('click', (event) => {
  const button = event.target.closest('button');
  if (!button) return;
  const { action, id } = button.dataset;
  if (action === 'toggle') toggleInterest(id);
  if (action === 'delete') deleteInterest(id);
});

loadInterests().catch(error => {
  console.error(error);
  alert('Failed to load interests. Is the local server running?');
});
