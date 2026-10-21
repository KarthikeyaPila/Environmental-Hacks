/* Backend bridge for the collection-partner workspace. */
(() => {
  const API_BASE = window.PHIR_API_BASE || '';
  let collectorId = window.phirIdentity?.idFor('kabadiwala') || 'kabadiwala_1';
  const areaIds = {};
  let selectedMapArea = null;
  let regionRowsShown = 6;
  let opportunityCardsShown = 6;
  let requestTableRowsShown = 8;
  let collectorDataReady = false;
  let mapFrameReady = false;
  let mapLoadError = '';
  let latestCollectorMetrics = null;
  let collectorRevision = 0;
  let collectorRefreshSequence = 0;
  const pendingRequestActions = new Set();
  const slug = name => `area_${name.toLowerCase().replaceAll(' ', '_')}`;
  const api = async (path, options = {}) => {
    const url = `${API_BASE}${path}`;
    if ((options.method || 'GET').toUpperCase() === 'GET' && window.phirApiRead) return window.phirApiRead(url);
    const response = await fetch(`${API_BASE}${path}`, {headers: {'Content-Type': 'application/json', ...(options.headers || {})}, ...options});
    const body = await response.json();
    if (!response.ok) throw new Error(body?.error?.message || 'The recovery service is unavailable.');
    window.phirApiInvalidate?.('/api/');
    return body;
  };
  const localOpportunity = item => {
    const materialIds = Object.keys(item.quantityByType || {}).map(type => `${item.requestId}:${type}`);
    return {id: item.requestId, status: item.status, isDemo: Boolean(item.isDemo), area: item.region || area, region: item.region || area, regionId: item.regionId, materialIds, quantityByType: item.quantityByType || {}, quantityKg: Object.values(item.quantityByType || {}).reduce((sum, value) => sum + Number(value), 0), estimatedValue: item.estimatedValueInr};
  };
  const revealCollector = () => setTimeout(() => document.documentElement.classList.remove('collector-pending'), 0);
  const districtId = name => name.toLowerCase().replaceAll(' ', '-');
  const selectableMapUrl = 'map/delhi-map-selectable.html';
  function updateMapLoading(message = 'Loading locality data…') {
    const map = document.querySelector('.phir-delhi-map');
    if (!map) return;
    let overlay = map.querySelector('.phir-map-loading');
    const loading = !mapLoadError && (!collectorDataReady || !mapFrameReady);
    if (!loading && !mapLoadError) { overlay?.remove(); return; }
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.className = 'phir-map-loading';
      overlay.setAttribute('role', 'status');
      overlay.setAttribute('aria-live', 'polite');
      map.append(overlay);
    }
    overlay.replaceChildren();
    if (mapLoadError) {
      const text = document.createElement('span');
      text.textContent = mapLoadError;
      const retry = document.createElement('button');
      retry.type = 'button'; retry.className = 'btn secondary'; retry.dataset.action = 'retry-map-data'; retry.textContent = 'Retry';
      overlay.append(text, retry);
    } else {
      const spinner = document.createElement('span'); spinner.className = 'phir-map-spinner'; spinner.setAttribute('aria-hidden', 'true');
      const text = document.createElement('span'); text.textContent = message;
      overlay.append(spinner, text);
    }
  }
  function applyOpportunityPagination() {
    const panel = document.querySelector('.map-layout > section:nth-child(2)');
    if (!panel) return;
    const cards = [...panel.querySelectorAll(':scope > article.opportunity')];
    cards.forEach((card, index) => { card.hidden = index >= opportunityCardsShown; });
    panel.querySelector('.phir-load-more-opportunities')?.remove();
    if (cards.length > opportunityCardsShown) {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'btn secondary phir-load-more-opportunities';
      button.dataset.action = 'load-more-opportunities';
      button.textContent = `Load more requests (${cards.length - opportunityCardsShown} remaining)`;
      panel.append(button);
    }
  }
  function applyRequestTablePagination() {
    const body = document.querySelector('#workspace-content .table-scroll tbody');
    if (!body) return;
    const rows = [...body.querySelectorAll('tr')];
    rows.forEach((row, index) => { row.hidden = index >= requestTableRowsShown; });
    body.closest('.table-scroll')?.parentElement?.querySelector('.phir-load-more-table')?.remove();
    if (rows.length > requestTableRowsShown) {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'btn secondary phir-load-more phir-load-more-table';
      button.dataset.action = 'load-more-table';
      button.textContent = `Load more requests (${rows.length - requestTableRowsShown} remaining)`;
      body.closest('.table-scroll').insertAdjacentElement('afterend', button);
    }
  }
  function paintCollectorStats() {
    const labels = [...document.querySelectorAll('.metrics .metric-label')];
    const values = labels.map(label => {
      const text = label.textContent.toLowerCase();
      if (text.includes('open opportunit')) return String(state.requests.filter(item => item.area === area && item.status === 'pending').length);
      if (text.includes('available collected')) return `${state.lots.filter(item => item.status === 'collected').reduce((total, item) => total + Number(item.quantityKg || 0), 0).toFixed(1)} kg`;
      if (text.includes('reserved for transfer')) return `${state.lots.filter(item => item.status === 'reserved').reduce((total, item) => total + Number(item.quantityKg || 0), 0).toFixed(1)} kg`;
      if (text.includes('transferred')) return `${Number(latestCollectorMetrics?.transferredToRecyclersKg || 0).toFixed(1)} kg`;
      return undefined;
    });
    window.phirPaintMetrics?.(values);
  }
  function addDemoBadges() {
    state.requests.forEach(request => {
      const card = [...document.querySelectorAll('.opportunity')].find(item => item.querySelector(`[data-id="${request.id}"]`));
      const head = card?.querySelector('.opportunity-head');
      if (request.isDemo && head && !head.querySelector('.data-origin-badge')) {
        const badge = document.createElement('span'); badge.className = 'badge data-origin-badge'; badge.textContent = 'Demo'; head.append(badge);
      }
    });
  }
  function addMapExperienceStyles() {
    if (document.getElementById('collector-map-experience-style')) return;
    const style = document.createElement('style');
    style.id = 'collector-map-experience-style';
    style.textContent = '.phir-delhi-map{position:relative}.phir-map-loading{position:absolute;inset:0;z-index:5;display:flex;align-items:center;justify-content:center;gap:12px;padding:20px;background:rgba(255,248,223,.9);color:#202363;font-weight:700;text-align:center}.phir-map-spinner{width:24px;height:24px;border:3px solid #008b7833;border-top-color:#008b78;border-radius:50%;animation:phir-map-spin .8s linear infinite}@keyframes phir-map-spin{to{transform:rotate(360deg)}}.phir-load-more{display:block;margin:14px auto 0}.opportunity[hidden]{display:none!important}.opportunity .data-origin-badge{margin-left:auto}.phir-profile-gate{padding:34px;text-align:center;border:1px dashed var(--line);border-radius:12px;background:var(--surface)}.phir-profile-gate h2{margin-top:0}';
    document.head.append(style);
  }
  function ensureLocalitySummary() {
    if (document.getElementById('collector-locality-summary-style')) return;
    const style = document.createElement('style');
    style.id = 'collector-locality-summary-style';
    style.textContent = '.dashboard-region-layout{align-items:start}.dashboard-region-layout>.collector-locality-summary{grid-column:2;grid-row:1;margin:0 0 20px;padding:22px 24px;border:2px solid var(--teal,#008b78);border-radius:18px;background:rgba(255,250,232,.9);box-shadow:4px 4px 0 var(--yellow,#ffd83d)}.dashboard-region-layout>.metrics{grid-column:1/-1;grid-row:2;display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:16px!important;align-items:stretch}.dashboard-region-layout>.metrics>*{width:auto!important;min-width:0!important;margin:0!important}.collector-locality-summary h3{margin:0 0 5px;color:var(--red,#cf1f3d)}.collector-locality-summary p{margin:0 0 16px}.collector-locality-summary-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.collector-locality-stat{padding:12px 14px;border:1px solid rgba(0,75,110,.25);border-radius:10px;background:rgba(255,255,255,.32)}.collector-locality-stat strong{display:block;font-size:1.2rem;color:var(--teal,#008b78);line-height:1.2}.collector-locality-stat span{font-size:.78rem}.collector-locality-stat:nth-child(3),.collector-locality-stat.mix{grid-column:1/-1}.collector-locality-stat.mix strong{font-size:1rem;line-height:1.35}.map-layout .note{display:none!important}@media(max-width:900px){.dashboard-region-layout>.collector-locality-summary{grid-column:1;grid-row:auto}.dashboard-region-layout>.metrics{grid-column:1;grid-row:auto;grid-template-columns:repeat(2,minmax(0,1fr))!important}}@media(max-width:800px){.collector-locality-summary-grid{grid-template-columns:1fr 1fr}}';
    document.head.appendChild(style);
    const alignmentStyle = document.createElement('style');
    alignmentStyle.textContent = '.dashboard-region-layout>.collector-locality-summary{margin-top:62px}@media(max-width:900px){.dashboard-region-layout>.collector-locality-summary{margin-top:0}}';
    document.head.appendChild(alignmentStyle);
  }
  const materialLabel = value => String(value || '').replaceAll('_', ' ').replace(/\b\w/g, letter => letter.toUpperCase());
  function hydrateCollectorProfile(profile) {
    const card = document.querySelector('.partner-profile-card');
    if (!card || !profile) return;
    const badge = card.querySelector('.partner-profile-identity .badge');
    const identity = card.querySelector('.partner-profile-identity');
    const sections = card.querySelectorAll('.partner-profile-details section');
    const note = card.querySelector('.partner-profile-note');
    const name = profile.name || 'Collection partner';
    if (badge) badge.textContent = 'Live profile';
    if (identity?.querySelector('h2')) identity.querySelector('h2').textContent = name;
    if (identity?.querySelector('p')) identity.querySelector('p').textContent = `Kabadiwala / Aggregator · ${profile.locality || 'Delhi'}`;
    if (sections[0]) {
      sections[0].querySelector('h3').textContent = 'Primary locality';
      sections[0].querySelector('.partner-profile-chips').innerHTML = `<span>${profile.locality || 'Delhi'}</span>`;
      sections[0].querySelector('p').textContent = 'Current locality in the recovery network.';
    }
    if (sections[1]) {
      sections[1].querySelector('.partner-profile-chips').innerHTML = (profile.supportedMaterials || []).map(material => `<span>${materialLabel(material)}</span>`).join('');
      sections[1].querySelector('p').textContent = 'Materials currently accepted by this partner.';
    }
    if (note) note.remove();
  }
  function renderRegionRequests(requests) {
    const panel = document.querySelector('.dashboard-map-detail');
    if (!panel) return;
    const selectedRegion = selectedMapArea;
    const visible = selectedRegion ? requests.filter(request => request.area === selectedRegion) : requests;
    const grouped = visible.reduce((result, request) => {
      const key = request.area || 'Unknown locality';
      const entry = result[key] || (result[key] = {count: 0, kg: 0});
      entry.count += 1;
      entry.kg += Number(request.quantityKg || 0);
      return result;
    }, {});
    const groupSummary = Object.entries(grouped).map(([name, value]) => `${name}: ${value.count} request${value.count === 1 ? '' : 's'} · ${value.kg.toFixed(1)} kg`).join(' · ');
    const rows = visible.slice(0, regionRowsShown).map(request => `<tr><td>${request.area || '—'}</td><td>${Number(request.quantityKg || 0).toFixed(1)} kg</td><td><span class="badge ${request.isDemo ? '' : 'active'}">${request.isDemo ? 'Demo' : 'Real'}</span> <span class="badge active">${request.status}</span></td><td>${request.isPreview ? '<span class="muted">Illustrative sample</span>' : request.status === 'accepted' ? `<button class="btn secondary" data-action="collect" data-id="${request.id}">Mark collected</button>` : request.status === 'pending' ? `<button class="btn secondary" data-action="accept" data-id="${request.id}">Accept</button>` : request.status === 'collected' ? 'Collection recorded' : request.status}</td></tr>`).join('');
    const demoCount = visible.filter(request => request.isDemo).length;
    const realCount = visible.length - demoCount;
    const originLabel = `${realCount ? `${realCount} real` : ''}${realCount && demoCount ? ' · ' : ''}${demoCount ? `${demoCount} demo` : ''} request${visible.length === 1 ? '' : 's'}` || 'No requests';
    panel.innerHTML = `<div class="section-heading"><h2>${selectedRegion || 'Delhi'}</h2><span class="badge">${originLabel}</span></div><p class="muted" style="margin:-10px 0 18px">${selectedRegion ? 'Selected locality requests' : 'Delhi-wide recovery requests'}${groupSummary ? ` · ${groupSummary}` : ''}</p>${rows ? `<div class="table-scroll"><table><thead><tr><th>Locality</th><th>Material</th><th>Status</th><th>Action</th></tr></thead><tbody>${rows}</tbody></table></div>${visible.length > regionRowsShown ? `<button class="btn secondary phir-load-more" data-action="load-more-region">Load more requests (${visible.length - regionRowsShown} remaining)</button>` : ''}` : `<div class="empty"><h3>No requests in this view.</h3><p>Select another district or add a collection request from Household.</p></div>`}`;
  }
  function mountSelectableMap() {
    addMapExperienceStyles();
    document.querySelectorAll('.workspace .map:not(.phir-delhi-map)').forEach(mapShell => {
      mapShell.classList.add('phir-delhi-map');
      const next = document.createElement('iframe');
      next.title = 'Selectable Delhi district collection map';
      next.src = selectableMapUrl;
      next.className = 'live-delhi-map-frame';
      mapFrameReady = false;
      next.addEventListener('load', () => { mapFrameReady = true; if (window.__phirCollectorAreas) installLiveMap(window.__phirCollectorAreas); updateMapLoading(); }, {once: true});
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
      mapFrameReady = false;
      next.addEventListener('load', () => { mapFrameReady = true; if (window.__phirCollectorAreas) installLiveMap(window.__phirCollectorAreas); updateMapLoading(); }, {once: true});
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
      mapFrameReady = false;
      frame.addEventListener('load', () => { mapFrameReady = true; installLiveMap(areas); updateMapLoading(); }, {once: true});
      return;
    }
    if (!frame) {
      const frame = document.createElement('iframe');
      frame.title = 'Selectable Delhi district collection map';
      frame.src = selectableMapUrl;
      frame.className = 'live-delhi-map-frame';
      mapFrameReady = false;
      frame.addEventListener('load', () => { mapFrameReady = true; installLiveMap(areas); updateMapLoading(); }, {once: true});
      mapShell?.prepend(frame);
      return;
    }
    if (!frame?.contentWindow?.DelhiMap) { mapFrameReady = false; updateMapLoading('Loading the Delhi map…'); return; }
    mapFrameReady = true;
    const map = frame.contentWindow.DelhiMap;
    if (!frame.dataset.phirBound) {
      frame.dataset.phirBound = 'true';
      frame.contentDocument.addEventListener('district-select', event => {
        const selected = event.detail;
        const match = selected && areas.areas.find(item => districtId(item.name) === selected.id);
        if (match) {
          selectedMapArea = match.name;
          area = match.name;
          regionRowsShown = 6;
          opportunityCardsShown = 6;
          refreshCollector().catch(error => toast(error.message));
        }
      });
    }
    frame.contentWindow.DelhiMap.pins.replaceChildren();
    updateMapLoading();
  }
  async function refreshCollector({silent = false} = {}) {
    const signedInProfile = window.phirIdentity?.profileFor('kabadiwala');
    if (!signedInProfile?.id) {
      collectorDataReady = true;
      const content = document.querySelector('#workspace-content');
      if (content && view === 'collector') content.innerHTML = '<section class="phir-profile-gate"><h2>Set up your collection-partner profile</h2><p>Enter your name and service area to open the collection workspace.</p><button class="btn" type="button" data-action="open-collector-profile">Create profile</button></section>';
      window.phirMarkWorkspaceReady?.();
      revealCollector();
      updateMapLoading();
      return;
    }
    collectorId = window.phirIdentity?.idFor('kabadiwala') || collectorId;
    mapLoadError = '';
    if (!silent) {
      collectorDataReady = false;
      updateMapLoading('Loading locality requests…');
    }
    const revision = collectorRevision;
    const sequence = ++collectorRefreshSequence;
    let areas, inventory, requests, metrics, profile;
    try {
      [areas, inventory, requests, metrics, profile] = await Promise.all([
        api('/api/demo/areas'),
        api(`/api/kabadiwalas/${collectorId}/inventory`),
        api(`/api/kabadiwalas/${collectorId}/requests`),
        api(`/api/kabadiwalas/${collectorId}/metrics`),
        api(`/api/kabadiwalas/${collectorId}/profile`),
      ]);
    } catch (error) {
      if (!silent) {
        mapLoadError = 'Could not load collection data. Check your connection and retry.';
        collectorDataReady = true;
        updateMapLoading();
      }
      throw error;
    }
    if (revision !== collectorRevision || sequence !== collectorRefreshSequence) return;
    window.__phirCollectorAreas = areas;
    areas.areas.forEach(item => { areaIds[item.name] = item.areaId || slug(item.name); });
    // Start the collection map on a locality with a real opportunity when
    // entering the role. Previously the household's default locality could
    // leave the map on an empty area while requests existed elsewhere.
    if (!areaIds[area]) area = areas.areas.find(item => item.requestCount > 0)?.name || areas.areas[0]?.name || area;
    const all = requests.requests.map(item => ({id: item.id, status: item.status, isDemo: Boolean(item.isDemo), area: item.region || area, region: item.region || area, regionId: item.regionId, materialIds: Object.keys(item.quantityByType || {}).map(type => `${item.id}:${type}`), quantityByType: item.quantityByType || {}, quantityKg: Object.values(item.quantityByType || {}).reduce((sum, value) => sum + Number(value), 0), estimatedValue: item.estimatedValueInr}));
    state.requests = all;
    state.materials = all.flatMap(request => Object.entries(request.quantityByType || {}).map(([type, quantity]) => ({id: `${request.id}:${type}`, type, quantityKg: Number(quantity), estimatedValue: null, status: request.status, owner: 'household'})));
    state.lots = inventory.inventory.map((item, index) => ({id: `inventory:${item.materialType}:${item.status || 'collected'}:${index}`, type: item.materialType, quantityKg: Number(item.quantityKg), status: item.status || 'collected', isDemo: Boolean(item.isDemo), partner: 'Your collection inventory', area}));
    render();
    window.phirMarkWorkspaceReady?.();
    renderRegionRequests(state.requests);
    applyOpportunityPagination();
    addDemoBadges();
    document.querySelectorAll('.section-heading').forEach(heading => {
      if (heading.querySelector('h3')?.textContent.trim() !== 'Neighbourhood preview') return;
      heading.nextElementSibling?.remove();
      heading.remove();
    });
    ensureLocalitySummary();
    const selectedLocality = areas.areas.find(item => item.name === selectedMapArea);
    const locality = selectedLocality || areas.areas.reduce((total, item) => {
      total.requestCount += Number(item.requestCount || 0);
      total.materialKg += Number(item.materialKg || 0);
      total.estimatedValueInr += Number(item.estimatedValueInr || 0);
      Object.entries(item.materialBreakdown || {}).forEach(([type, value]) => { total.materialBreakdown[type] = (total.materialBreakdown[type] || 0) + Number(value || 0); });
      return total;
    }, {name: 'Delhi', requestCount: 0, materialKg: 0, estimatedValueInr: 0, materialBreakdown: {}});
    const paintLocalitySummary = () => {
      document.querySelectorAll('.note').forEach(note => {
        if (note.textContent.includes('illustrated locality preview') || note.textContent.includes('Density labels')) note.remove();
      });
      const localityPanel = document.querySelector('.dashboard-region-layout') || document.querySelector('.map-layout > section:nth-child(2)');
      if (!localityPanel) return;
      document.querySelectorAll('.collector-locality-summary').forEach(existing => { if (existing.parentElement !== localityPanel) existing.remove(); });
      let summary = localityPanel.querySelector('.collector-locality-summary');
      if (!summary) { summary = document.createElement('div'); summary.className = 'collector-locality-summary'; localityPanel.append(summary); }
      const materials = Object.entries(locality.materialBreakdown || {}).map(([type, value]) => `${type.replaceAll('_', ' ')} ${Number(value).toFixed(1)} kg`).join(' · ') || 'No material recorded yet';
      summary.innerHTML = `<h3>${locality.name}</h3><p>${selectedLocality ? 'Selected locality overview' : 'Delhi-wide recovery overview'}</p><div class="collector-locality-summary-grid"><div class="collector-locality-stat"><strong>${locality.requestCount || 0}</strong><span>household requests</span></div><div class="collector-locality-stat"><strong>${Number(locality.materialKg || 0).toFixed(1)} kg</strong><span>material available</span></div><div class="collector-locality-stat"><strong>₹${locality.estimatedValueInr || 0}</strong><span>estimated value</span></div><div class="collector-locality-stat mix"><strong>${materials}</strong><span>material mix</span></div></div>`;
    };
    paintLocalitySummary();
    [0, 100, 500].forEach(delay => setTimeout(paintLocalitySummary, delay));
    latestCollectorMetrics = metrics;
    paintCollectorStats();
    window.phirCollectorProfile = profile;
    [0, 100, 500].forEach(delay => setTimeout(() => hydrateCollectorProfile(profile), delay));
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
    collectorDataReady = true;
    updateMapLoading();
  }
  async function run(action, success, button, requestId, nextStatus) {
    if (pendingRequestActions.has(requestId)) return;
    pendingRequestActions.add(requestId);
    collectorRevision += 1;
    const requestIndex = state.requests.findIndex(item => item.id === requestId);
    const request = requestIndex >= 0 ? state.requests[requestIndex] : null;
    const previousRequest = request && {...request, quantityByType: {...request.quantityByType}};
    const inventoryDeltas = [];
    if (request) {
      if (nextStatus === 'rejected') state.requests = state.requests.filter(item => item.id !== requestId);
      else {
        request.status = nextStatus;
        if (nextStatus === 'collected') {
          Object.entries(request.quantityByType || {}).forEach(([type, quantity]) => {
            const lot = state.lots.find(item => item.type === type && item.status === 'collected');
            if (lot) { lot.quantityKg += Number(quantity); inventoryDeltas.push({id: lot.id, type, quantity: Number(quantity)}); }
            else {
              const optimisticLot = {id:`optimistic:${requestId}:${type}`,type,quantityKg:Number(quantity),status:'collected',partner:'Your collection inventory',area};
              state.lots.push(optimisticLot);
              inventoryDeltas.push({id: optimisticLot.id, type, quantity: Number(quantity), created: true});
            }
          });
        }
      }
      render();
      renderRegionRequests(state.requests);
      applyOpportunityPagination();
      addDemoBadges();
      paintCollectorStats();
      window.phirMarkWorkspaceReady?.();
    }
    document.querySelectorAll(`[data-id="${CSS.escape(requestId)}"]`).forEach(control => { if (control.matches('button')) control.disabled = true; });
    if (button) { button.disabled = true; button.dataset.busy = 'true'; }
    try {
      await Promise.all([action(), new Promise(resolve => setTimeout(resolve, 650))]);
      collectorRevision += 1;
      toast(success);
      refreshCollector({silent: true}).catch(error => console.warn('Background collection refresh failed:', error));
    }
    catch (error) {
      collectorRevision += 1;
      if (previousRequest) {
        const currentIndex = state.requests.findIndex(item => item.id === requestId);
        if (currentIndex >= 0) state.requests[currentIndex] = previousRequest;
        else state.requests.splice(Math.min(requestIndex, state.requests.length), 0, previousRequest);
      }
      inventoryDeltas.forEach(delta => {
        const lot = state.lots.find(item => item.id === delta.id);
        if (!lot) return;
        if (delta.created) state.lots = state.lots.filter(item => item.id !== delta.id);
        else lot.quantityKg = Math.max(0, lot.quantityKg - delta.quantity);
      });
      render(); renderRegionRequests(state.requests); applyOpportunityPagination(); addDemoBadges(); paintCollectorStats();
      toast(error.message);
    }
    finally {
      pendingRequestActions.delete(requestId);
      if (button) { button.disabled = false; delete button.dataset.busy; }
    }
  }
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-action]');
    if (!button || view !== 'collector') return;
    const action = button.dataset.action, id = button.dataset.id;
    if (action === 'open-collector-profile') {
      event.preventDefault(); event.stopImmediatePropagation();
      window.phirOpenIdentityPicker?.('kabadiwala');
      return;
    }
    if (action === 'retry-map-data') {
      event.preventDefault(); event.stopImmediatePropagation();
      refreshCollector().catch(error => toast(error.message));
      return;
    }
    if (action === 'load-more-region') {
      event.preventDefault(); event.stopImmediatePropagation(); regionRowsShown += 6; renderRegionRequests(state.requests); return;
    }
    if (action === 'load-more-opportunities') {
      event.preventDefault(); event.stopImmediatePropagation(); opportunityCardsShown += 6; applyOpportunityPagination(); return;
    }
    if (action === 'load-more-table') {
      event.preventDefault(); event.stopImmediatePropagation(); requestTableRowsShown += 8; applyRequestTablePagination(); return;
    }
    if (['accept', 'reject', 'collect', 'reject-confirmed', 'collect-confirmed'].includes(action)) {
      event.preventDefault(); event.stopImmediatePropagation();
      if (action === 'reject' || action === 'reject-confirmed') {
        run(() => api(`/api/collection-requests/${id}/reject`, {method: 'POST', body: JSON.stringify({kabadiwalaId: collectorId})}), 'Request declined.', button, id, 'rejected');
      } else if (action === 'accept') {
        run(() => api(`/api/collection-requests/${id}/accept`, {method: 'POST', body: JSON.stringify({kabadiwalaId: collectorId})}), 'Request accepted.', button, id, 'accepted');
      } else {
        run(() => api(`/api/collection-requests/${id}/collect`, {method: 'POST', body: JSON.stringify({kabadiwalaId: collectorId})}), 'Collection recorded.', button, id, 'collected');
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
      regionRowsShown = 6;
      opportunityCardsShown = 6;
      setTimeout(() => refreshCollector().catch(error => toast(error.message)), 0);
    }
  }, true);
  const originalGo = go;
  const originalRender = render;
  render = function() {
    // Accept/reject updates replace the whole workspace through the legacy
    // renderer, which otherwise forces the viewport back to the page top.
    // Keep the current position on collector re-renders, but not when entering
    // the collector role from another page.
    const keepPosition = Boolean(document.querySelector('.workspace[data-theme="collector"]'));
    const scrollTop = window.scrollY;
    originalRender();
    if (keepPosition) window.scrollTo(0, scrollTop);
    if (view === 'collector') setTimeout(() => { applyRequestTablePagination(); applyOpportunityPagination(); addDemoBadges(); }, 0);
  };
  go = function(next) { originalGo(next); if (next === 'collector') refreshCollector().catch(error => { document.documentElement.classList.remove('collector-pending'); toast(error.message); }); };
  window.phirRefreshCollector = () => refreshCollector().catch(error => toast(error.message));
  window.addEventListener('phir-profile-updated', event => { if (event.detail?.role === 'kabadiwala') window.phirRefreshCollector(); });
  function warmAreaSummariesOnChooser() {
    if (view !== 'select') return;
    window.phirApiWarm?.('/api/demo/areas');
    const profile = window.phirIdentity?.profileFor('kabadiwala');
    if (!profile?.id) return;
    for (const resource of ['inventory', 'requests', 'metrics', 'profile']) {
      window.phirApiWarm?.(`/api/kabadiwalas/${profile.id}/${resource}`);
    }
  }
  new MutationObserver(warmAreaSummariesOnChooser).observe(document.querySelector('#app') || document.body, {childList: true, subtree: true});
  warmAreaSummariesOnChooser();
  if (view === 'collector') refreshCollector().catch(error => { document.documentElement.classList.remove('collector-pending'); toast(error.message); });
})();
