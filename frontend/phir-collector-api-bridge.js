/* Backend bridge for the collection-partner workspace. */
(() => {
  const API_BASE = window.PHIR_API_BASE || '';
  const collectorId = 'kabadiwala_1';
  const areaIds = {};
  const slug = name => `area_${name.toLowerCase().replaceAll(' ', '_')}`;
  const api = async (path, options = {}) => {
    const response = await fetch(`${API_BASE}${path}`, {headers: {'Content-Type': 'application/json', ...(options.headers || {})}, ...options});
    const body = await response.json();
    if (!response.ok) throw new Error(body?.error?.message || 'The recovery service is unavailable.');
    return body;
  };
  const localOpportunity = item => {
    const materialIds = Object.keys(item.quantityByType || {}).map(type => `${item.requestId}:${type}`);
    return {id: item.requestId, status: item.status, area, materialIds, quantityByType: item.quantityByType || {}, quantityKg: Object.values(item.quantityByType || {}).reduce((sum, value) => sum + Number(value), 0), estimatedValue: item.estimatedValueInr};
  };
  async function refreshCollector() {
    const [areas, inventory, requests, metrics, profile] = await Promise.all([
      api(`/api/kabadiwalas/${collectorId}/areas`),
      api(`/api/kabadiwalas/${collectorId}/inventory`),
      api(`/api/kabadiwalas/${collectorId}/requests`),
      api(`/api/kabadiwalas/${collectorId}/metrics`),
      api(`/api/kabadiwalas/${collectorId}/profile`),
    ]);
    areas.areas.forEach(item => { areaIds[item.name] = item.areaId || slug(item.name); });
    if (!areaIds[area]) area = areas.areas[0]?.name || area;
    const selected = areas.areas.find(item => item.name === area);
    const opportunities = selected ? await api(`/api/kabadiwalas/${collectorId}/areas/${selected.areaId}/opportunities`) : {opportunities: []};
    const all = requests.requests.map(item => ({id: item.id, status: item.status, area, materialIds: [], quantityByType: item.quantityByType || {}, quantityKg: Object.values(item.quantityByType || {}).reduce((sum, value) => sum + Number(value), 0), estimatedValue: item.estimatedValueInr}));
    const visible = opportunities.opportunities.map(localOpportunity);
    state.requests = [...visible, ...all.filter(item => !visible.some(current => current.id === item.id))];
    state.materials = [...visible, ...all].flatMap(request => Object.entries(request.quantityByType || {}).map(([type, quantity]) => ({id: `${request.id}:${type}`, type, quantityKg: Number(quantity), estimatedValue: null, status: request.status, owner: 'household'})));
    state.lots = inventory.inventory.map(item => ({id: `inventory:${item.materialType}`, type: item.materialType, quantityKg: Number(item.quantityKg), status: 'collected', partner: 'Your collection inventory', area}));
    render();
    window.phirPaintMetrics?.([`${metrics.requestsAccepted}`, `${metrics.totalCollectedKg} kg`, `₹${metrics.estimatedRevenueInr}`, `${metrics.collectionsCompleted}`]);
    window.phirCollectorProfile = profile;
    const map = document.querySelector('.map');
    if (map) {
      map.querySelectorAll('.map-pin').forEach(pin => pin.remove());
      map.insertAdjacentHTML('beforeend', areas.areas.map(item => `<button class="map-pin ${area === item.name ? 'selected' : ''}" data-action="area" data-area="${item.name}" aria-label="Explore ${item.name}">${item.name}<br>${item.materialKg || 0} kg · ${item.requestCount || 0} requests</button>`).join(''));
    }
  }
  async function run(action, success) {
    try { await action(); await refreshCollector(); toast(success); }
    catch (error) { toast(error.message); }
  }
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-action]');
    if (!button || view !== 'collector') return;
    const action = button.dataset.action, id = button.dataset.id;
    if (['accept', 'reject', 'collect', 'reject-confirmed', 'collect-confirmed'].includes(action)) {
      event.preventDefault(); event.stopImmediatePropagation();
      if (action === 'reject' || action === 'reject-confirmed') {
        run(() => api(`/api/collection-requests/${id}/reject`, {method: 'POST', body: JSON.stringify({kabadiwalaId: collectorId})}), 'Request declined.');
      } else if (action === 'accept') {
        run(() => api(`/api/collection-requests/${id}/accept`, {method: 'POST', body: JSON.stringify({kabadiwalaId: collectorId})}), 'Request accepted.');
      } else {
        run(() => api(`/api/collection-requests/${id}/collect`, {method: 'POST', body: JSON.stringify({kabadiwalaId: collectorId})}), 'Collection recorded.');
      }
    } else if (action === 'plan-route') {
      event.preventDefault(); event.stopImmediatePropagation();
      const selected = [...selectedStops].filter(requestId => state.requests.some(request => request.id === requestId && request.area === area && request.status !== 'collected'));
      if (!selected.length) { toast('Select at least one open request as a route stop.'); return; }
      api(`/api/kabadiwalas/${collectorId}/route`, {method: 'POST', body: JSON.stringify({areaId: areaIds[area], requestIds: selected, optimizeFor: 'distance'})}).then(result => {
        const target = $('#route-result');
        if (target) target.innerHTML = `<div class="route-preview"><h3>${selected.length} selected stop${selected.length === 1 ? '' : 's'} · ${area}</h3><p>${(result.stops || []).map(stop => `${stop.stopNumber || ''}. Area-level pickup · ${stop.requestId || ''}`).join('<br>')}</p><p class="muted">Local preview · ${result.totalDistanceKm ?? '—'} km · ${result.estimatedDurationMinutes ?? '—'} min estimated. Exact household locations remain private.</p></div>`;
        toast('Route preview generated.');
      }).catch(error => toast(error.message));
    } else if (action === 'area') {
      area = button.dataset.area;
      setTimeout(() => refreshCollector().catch(error => toast(error.message)), 0);
    }
  }, true);
  const originalGo = go;
  go = function(next) { originalGo(next); if (next === 'collector') refreshCollector().catch(error => toast(error.message)); };
  if (view === 'collector') refreshCollector().catch(error => toast(error.message));
})();
