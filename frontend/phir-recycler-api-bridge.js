/* Backend bridge for the recycler workspace. */
(() => {
  const API_BASE = window.PHIR_API_BASE || '';
  const recyclerId = 'recycler_1';
  const api = async (path, options = {}) => {
    const response = await fetch(`${API_BASE}${path}`, {headers: {'Content-Type': 'application/json', ...(options.headers || {})}, ...options});
    const body = await response.json();
    if (!response.ok) throw new Error(body?.error?.message || 'The recovery service is unavailable.');
    return body;
  };
  const localRequirement = item => ({id: item.id, type: item.materialType, quantityKg: Number(item.requiredQuantityKg), minimumKg: Number(item.minimumQuantityKg || 0), fulfilledKg: Number(item.fulfilledQuantityKg || 0), company: state.company.name, status: item.status});
  const localBooking = item => ({id: item.id, type: item.materialType, quantityKg: Number(item.quantityKg), partner: item.kabadiwalaId, requirementId: item.requirementId, status: item.status === 'confirmed' ? 'confirmed' : item.status === 'completed' ? 'completed' : item.status});
  const materialLabel = value => String(value || '').replaceAll('_', ' ').replace(/\b\w/g, letter => letter.toUpperCase());
  function hydrateMarketplace() {
    document.querySelectorAll('.lot-card').forEach((card, index) => {
      const lot = state.lots[index];
      if (!lot) return;
      const matches = state.requirements.filter(requirement => requirement.type === lot.type && requirement.status !== 'fulfilled');
      const status = card.querySelector('.lot-meta span:last-child');
      const statusText = matches.length ? `Matches ${matches.length} open requirement${matches.length === 1 ? '' : 's'}` : 'No current requirement match';
      if (status && status.textContent !== statusText) status.textContent = statusText;
      const button = card.querySelector('[data-action="reserve"]');
      if (button && !matches.length) {
        if (button.textContent.trim() !== 'View material') button.textContent = 'View material';
        button.disabled = true;
        button.title = 'Publish a matching requirement before reserving this material.';
      }
    });
  }
  function polishRecyclerView() {
    if (view !== 'recycler') return;
    document.querySelectorAll('.note').forEach(note => {
      if (note.textContent.includes('Sample records for the presentation') || note.textContent.includes('Added material has no live quote')) note.remove();
    });
    if (tab === 'Material marketplace') document.querySelectorAll('.dashboard-reference-section').forEach(section => section.remove());
    document.querySelectorAll('.metrics .metric-label').forEach(label => {
      const labels = {'Available in sample marketplace': 'Available collected material', 'Confirmed transfers': 'Confirmed handovers'};
      if (labels[label.textContent.trim()] && label.textContent !== labels[label.textContent.trim()]) label.textContent = labels[label.textContent.trim()];
    });
    if (tab === 'Requirements') document.querySelectorAll('.requirement-row').forEach((row, index) => {
      const requirement = state.requirements[index];
      if (!requirement) return;
      const availableKg = state.lots.filter(lot => lot.type === requirement.type).reduce((total, lot) => total + lot.quantityKg, 0);
      const description = row.querySelector('p');
      const descriptionText = `${Math.max(0, requirement.quantityKg - requirement.fulfilledKg).toFixed(1)} kg still needed · ${availableKg.toFixed(1)} kg available now · Delhi`;
      if (description && description.textContent !== descriptionText) description.textContent = descriptionText;
    });
  }
  async function refreshRecycler() {
    const [requirements, available, bookings, metrics, profile] = await Promise.all([
      api(`/api/recyclers/${recyclerId}/requirements`),
      api(`/api/recyclers/${recyclerId}/available-material`),
      api(`/api/recyclers/${recyclerId}/bookings`),
      api(`/api/recyclers/${recyclerId}/metrics`),
      api(`/api/recyclers/${recyclerId}/profile`),
    ]);
    state.company = {name: profile.name, locality: profile.locality, contact: profile.contact || ''};
    state.requirements = requirements.requirements.map(localRequirement);
    state.lots = available.availableMaterial.map(item => ({id: `${item.kabadiwalaId}:${item.materialType}`, type: item.materialType, quantityKg: Number(item.quantityKg), partner: item.kabadiwalaName || item.kabadiwalaId, area: item.region || 'Delhi', regionId: item.regionId, status: 'collected'}));
    state.bookings = bookings.bookings.map(localBooking);
    render();
    [0, 100, 500].forEach(delay => setTimeout(() => { polishRecyclerView(); hydrateMarketplace(); }, delay));
    window.phirPaintMetrics?.([`${metrics.reservedBookings}`, `${metrics.fulfilledQuantityKg} kg`, `${metrics.completedBookings}`, `${metrics.requirements.length}`]);
  }
  async function run(action, success) {
    document.querySelectorAll('button[data-action], button[type="submit"]').forEach(button => { button.disabled = true; button.dataset.busy = 'true'; });
    try { await action(); await refreshRecycler(); if (modal.open) modal.close(); toast(success); }
    catch (error) { if (modal.open && $('#form-error', modal)) $('#form-error', modal).textContent = error.message; else toast(error.message); }
    finally { document.querySelectorAll('button[data-busy="true"]').forEach(button => { button.disabled = false; delete button.dataset.busy; }); }
  }
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-action]');
    if (!button || view !== 'recycler') return;
    const action = button.dataset.action;
    if (action === 'confirm-booking') {
      event.preventDefault(); event.stopImmediatePropagation();
      run(() => api(`/api/bookings/${button.dataset.id}/confirm`, {method: 'POST', body: JSON.stringify({recyclerId})}), 'Handover recorded.');
    }
  }, true);
  document.addEventListener('submit', event => {
    const form = event.target;
    if (view !== 'recycler') return;
    if (form.id === 'requirement-form') {
      event.preventDefault(); event.stopImmediatePropagation();
      const data = new FormData(form);
      run(() => api('/api/recycler-requirements', {method: 'POST', body: JSON.stringify({recyclerId, materialType: data.get('type'), requiredQuantityKg: Number(data.get('weight')), minimumQuantityKg: Number(data.get('minimum') || 0)})}), 'Requirement published.');
    } else if (form.id === 'company-form') {
      event.preventDefault(); event.stopImmediatePropagation();
      const data = new FormData(form);
      run(() => api(`/api/recyclers/${recyclerId}/profile`, {method: 'POST', body: JSON.stringify({recyclerId, name: data.get('name'), locality: data.get('locality'), contact: data.get('contact')})}), 'Company profile saved.');
    } else if (form.id === 'booking-form') {
      event.preventDefault(); event.stopImmediatePropagation();
      const data = new FormData(form), [kabadiwalaId, materialType] = String(form.dataset.id).split(':');
      const lot = state.lots.find(item => item.id === form.dataset.id);
      run(() => api('/api/bookings', {method: 'POST', body: JSON.stringify({recyclerId, requirementId: data.get('requirement'), kabadiwalaId, quantityKg: Number(data.get('quantity'))})}), 'Material reserved.');
    }
  }, true);
  const originalGo = go;
  go = function(next) { originalGo(next); if (next === 'recycler') refreshRecycler().catch(error => toast(error.message)); };
  if (view === 'recycler') refreshRecycler().catch(error => toast(error.message));
  new MutationObserver(() => { if (view === 'recycler') polishRecyclerView(); }).observe(document.querySelector('#app'), {childList: true, subtree: true});
})();
