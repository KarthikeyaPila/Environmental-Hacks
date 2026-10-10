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
  async function refreshRecycler() {
    const [requirements, available, bookings, metrics] = await Promise.all([
      api(`/api/recyclers/${recyclerId}/requirements`),
      api(`/api/recyclers/${recyclerId}/available-material`),
      api(`/api/recyclers/${recyclerId}/bookings`),
      api(`/api/recyclers/${recyclerId}/metrics`),
    ]);
    state.requirements = requirements.requirements.map(localRequirement);
    state.lots = available.availableMaterial.map(item => ({id: `${item.kabadiwalaId}:${item.materialType}`, type: item.materialType, quantityKg: Number(item.quantityKg), partner: item.kabadiwalaName || item.kabadiwalaId, area: item.region || 'Delhi', regionId: item.regionId, status: 'collected'}));
    state.bookings = bookings.bookings.map(localBooking);
    render();
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
})();
