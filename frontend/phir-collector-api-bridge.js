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
    return {id: item.requestId, status: item.status, area: item.region || area, region: item.region || area, regionId: item.regionId, materialIds, quantityByType: item.quantityByType || {}, quantityKg: Object.values(item.quantityByType || {}).reduce((sum, value) => sum + Number(value), 0), estimatedValue: item.estimatedValueInr};
  };
  const revealCollector = () => setTimeout(() => document.documentElement.classList.remove('collector-pending'), 0);
  const districtId = name => name.toLowerCase().replaceAll(' ', '-');
  const selectableMapUrl = 'map/delhi-map-selectable.html';
  function mountSelectableMap() {
    document.querySelectorAll('.workspace .map:not(.phir-delhi-map)').forEach(mapShell => {
      mapShell.classList.add('phir-delhi-map');
      const next = document.createElement('iframe');
      next.title = 'Selectable Delhi district collection map';
      next.src = selectableMapUrl;
      next.className = 'live-delhi-map-frame';
      next.addEventListener('load', () => window.__phirCollectorAreas && installLiveMap(window.__phirCollectorAreas), {once: true});
      mapShell.replaceChildren(next);
    });
    document.querySelectorAll('.workspace .phir-delhi-map').forEach(mapShell => {
      const frame = mapShell.querySelector('iframe');
      if (frame?.src.includes('delhi-map-selectable.html')) return;
      const oldMap = frame || mapShell.querySelector('img');
      if (!oldMap) return;
      const next = document.createElement('iframe');
      next.title = 'Selectable Delhi district collection map';
      next.src = selectableMapUrl;
      next.className = 'live-delhi-map-frame';
      next.addEventListener('load', () => window.__phirCollectorAreas && installLiveMap(window.__phirCollectorAreas), {once: true});
      oldMap.replaceWith(next);
    });
  }
  new MutationObserver(mountSelectableMap).observe(document.querySelector('#app'), {childList: true, subtree: true});
  mountSelectableMap();
  function installLiveMap(areas) {
    const mapShell = document.querySelector('.phir-delhi-map');
    let frame = mapShell?.querySelector('iframe');
    const isSelectable = frame?.src.includes('delhi-map-selectable.html');
    if (frame && !isSelectable) {
      const oldMap = frame;
      frame = document.createElement('iframe');
      frame.title = 'Selectable Delhi district collection map';
      frame.src = selectableMapUrl;
      frame.className = 'live-delhi-map-frame';
      oldMap.replaceWith(frame);
      frame.addEventListener('load', () => installLiveMap(areas), {once: true});
      return;
    }
    if (!frame) {
      const frame = document.createElement('iframe');
      frame.title = 'Selectable Delhi district collection map';
      frame.src = selectableMapUrl;
      frame.className = 'live-delhi-map-frame';
      frame.addEventListener('load', () => installLiveMap(areas), {once: true});
      mapShell?.prepend(frame);
      return;
    }
    if (!frame?.contentWindow?.DelhiMap) return;
    const map = frame.contentWindow.DelhiMap;
    if (!frame.dataset.phirBound) {
      frame.dataset.phirBound = 'true';
      frame.contentDocument.addEventListener('district-select', event => {
        const selected = event.detail;
        const match = selected && areas.areas.find(item => districtId(item.name) === selected.id);
        if (match && area !== match.name) {
          area = match.name;
          refreshCollector().catch(error => toast(error.message));
        }
      });
    }
    map.pins.replaceChildren();
    if (!frame.contentDocument.getElementById('phir-live-pin-style')) {
      const style = frame.contentDocument.createElement('style');
      style.id = 'phir-live-pin-style';
      style.textContent = '.live-request-pin{pointer-events:none}.live-request-pin circle{fill:#c91f3d;stroke:#fff;stroke-width:2.5}.live-request-pin.selected circle{fill:#008c78}.live-request-pin text{fill:#fff;font:700 13px system-ui,sans-serif;text-anchor:middle;dominant-baseline:middle}';
      frame.contentDocument.head.append(style);
    }
    areas.areas.filter(item => item.requestCount > 0).forEach(item => {
      const district = frame.contentDocument.querySelector(`[data-district="${item.name}"]`);
      const cx = Number(district?.dataset.cx || 0), cy = Number(district?.dataset.cy || 0);
      if (!cx || !cy) return;
      const group = frame.contentDocument.createElementNS('http://www.w3.org/2000/svg', 'g');
      group.setAttribute('transform', `translate(${cx} ${cy})`);
      group.setAttribute('class', `live-request-pin ${area === item.name ? 'selected' : ''}`);
      group.innerHTML = `<circle r="17"/><text y="4">${item.requestCount}</text>`;
      map.pins.append(group);
    });
  }
  async function refreshCollector() {
    const [areas, inventory, requests, metrics, profile] = await Promise.all([
      api(`/api/kabadiwalas/${collectorId}/areas`),
      api(`/api/kabadiwalas/${collectorId}/inventory`),
      api(`/api/kabadiwalas/${collectorId}/requests`),
      api(`/api/kabadiwalas/${collectorId}/metrics`),
      api(`/api/kabadiwalas/${collectorId}/profile`),
    ]);
    window.__phirCollectorAreas = areas;
    areas.areas.forEach(item => { areaIds[item.name] = item.areaId || slug(item.name); });
    // Start the collection map on a locality with a real opportunity when
    // entering the role. Previously the household's default locality could
    // leave the map on an empty area while requests existed elsewhere.
    if (!areaIds[area]) area = areas.areas.find(item => item.requestCount > 0)?.name || areas.areas[0]?.name || area;
    const selected = areas.areas.find(item => item.name === area);
    const opportunities = selected ? await api(`/api/kabadiwalas/${collectorId}/areas/${selected.areaId}/opportunities`) : {opportunities: []};
    const all = requests.requests.map(item => ({id: item.id, status: item.status, area: item.region || area, region: item.region || area, regionId: item.regionId, materialIds: [], quantityByType: item.quantityByType || {}, quantityKg: Object.values(item.quantityByType || {}).reduce((sum, value) => sum + Number(value), 0), estimatedValue: item.estimatedValueInr}));
    const visible = opportunities.opportunities.map(localOpportunity);
    state.requests = [...visible, ...all.filter(item => !visible.some(current => current.id === item.id))];
    state.materials = [...visible, ...all].flatMap(request => Object.entries(request.quantityByType || {}).map(([type, quantity]) => ({id: `${request.id}:${type}`, type, quantityKg: Number(quantity), estimatedValue: null, status: request.status, owner: 'household'})));
    state.lots = inventory.inventory.map(item => ({id: `inventory:${item.materialType}`, type: item.materialType, quantityKg: Number(item.quantityKg), status: 'collected', partner: 'Your collection inventory', area}));
    render();
    window.phirPaintMetrics?.([`${metrics.requestsAccepted}`, `${metrics.totalCollectedKg} kg`, `₹${metrics.estimatedRevenueInr}`, `${metrics.collectionsCompleted}`]);
    window.phirCollectorProfile = profile;
    const map = document.querySelector('.map');
    if (map) {
      let summary = map.parentElement?.querySelector('.collector-map-summary');
      if (!summary) {
        summary = document.createElement('p');
        summary.className = 'collector-map-summary muted';
        map.insertAdjacentElement('afterend', summary);
      }
      const requestSummary = areas.requestSummary || {};
      summary.textContent = `${requestSummary.open || 0} open requests · ${requestSummary.total || 0} total recorded · ${requestSummary.accepted || 0} accepted · ${requestSummary.collected || 0} collected`;
      const caption = map.querySelector('.delhi-map-caption');
      if (caption) caption.textContent = 'LIVE COLLECTION OPPORTUNITIES · Pins show current open requests from the recovery database';
      installLiveMap(areas);
      const frame = map.querySelector('iframe');
      if (frame && !frame.contentWindow?.DelhiMap) frame.addEventListener('load', () => installLiveMap(areas), {once: true});
    }
    revealCollector();
  }
  async function run(action, success) {
    document.querySelectorAll('button[data-action]').forEach(button => { button.disabled = true; button.dataset.busy = 'true'; });
    try { await action(); await refreshCollector(); toast(success); }
    catch (error) { toast(error.message); }
    finally { document.querySelectorAll('button[data-busy="true"]').forEach(button => { button.disabled = false; delete button.dataset.busy; }); }
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
  go = function(next) { originalGo(next); if (next === 'collector') refreshCollector().catch(error => { document.documentElement.classList.remove('collector-pending'); toast(error.message); }); };
  if (view === 'collector') refreshCollector().catch(error => { document.documentElement.classList.remove('collector-pending'); toast(error.message); });
})();
