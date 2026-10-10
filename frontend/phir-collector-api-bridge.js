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
  function ensureLocalitySummary() {
    if (document.getElementById('collector-locality-summary-style')) return;
    const style = document.createElement('style');
    style.id = 'collector-locality-summary-style';
    style.textContent = '.collector-locality-summary{grid-column:1/-1;margin:0 0 16px;padding:18px 20px;border:2px solid var(--teal,#008b78);border-radius:18px;background:rgba(255,250,232,.9);box-shadow:4px 4px 0 var(--yellow,#ffd83d)}.collector-locality-summary h3{margin:0 0 5px;color:var(--red,#cf1f3d)}.collector-locality-summary p{margin:0 0 14px}.collector-locality-summary-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.collector-locality-stat{padding:10px 12px;border:1px solid rgba(0,75,110,.25);border-radius:10px;background:rgba(255,255,255,.32)}.collector-locality-stat strong{display:block;font-size:1.15rem;color:var(--teal,#008b78)}.collector-locality-stat span{font-size:.78rem}.map-layout .note{display:none!important}@media(max-width:800px){.collector-locality-summary-grid{grid-template-columns:1fr 1fr}}';
    document.head.appendChild(style);
  }
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
    frame.contentWindow.DelhiMap.pins.replaceChildren();
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
    ensureLocalitySummary();
    const locality = areas.areas.find(item => item.name === area) || {name: area, requestCount: 0, materialKg: 0, estimatedValueInr: 0, materialBreakdown: {}};
    const paintLocalitySummary = () => {
      document.querySelectorAll('.note').forEach(note => {
        if (note.textContent.includes('illustrated locality preview') || note.textContent.includes('Density labels')) note.remove();
      });
      const localityPanel = document.querySelector('.dashboard-region-layout > .metrics') || document.querySelector('.map-layout > section:nth-child(2)');
      if (!localityPanel) return;
      document.querySelectorAll('.collector-locality-summary').forEach(existing => { if (existing.parentElement !== localityPanel) existing.remove(); });
      let summary = localityPanel.querySelector('.collector-locality-summary');
      if (!summary) { summary = document.createElement('div'); summary.className = 'collector-locality-summary'; localityPanel.prepend(summary); }
      const materials = Object.entries(locality.materialBreakdown || {}).map(([type, value]) => `${type.replaceAll('_', ' ')} ${Number(value).toFixed(1)} kg`).join(' · ') || 'No material recorded yet';
      summary.innerHTML = `<h3>${locality.name}</h3><p>Selected locality overview</p><div class="collector-locality-summary-grid"><div class="collector-locality-stat"><strong>${locality.requestCount || 0}</strong><span>household requests</span></div><div class="collector-locality-stat"><strong>${Number(locality.materialKg || 0).toFixed(1)} kg</strong><span>material available</span></div><div class="collector-locality-stat"><strong>₹${locality.estimatedValueInr || 0}</strong><span>estimated value</span></div><div class="collector-locality-stat"><strong>${materials}</strong><span>material mix</span></div></div>`;
    };
    paintLocalitySummary();
    [0, 100, 500].forEach(delay => setTimeout(paintLocalitySummary, delay));
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
