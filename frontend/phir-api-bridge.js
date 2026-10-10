/* Backend bridge for the primary Phir frontend. */
(() => {
  const API_BASE = window.PHIR_API_BASE || '';
  const householdId = 'household_1';
  const api = async (path, options = {}) => {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: {'Content-Type': 'application/json', ...(options.headers || {})},
      ...options,
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body?.error?.message || 'The recovery service is unavailable.');
    return body;
  };
  const localMaterial = item => ({id: item.id, type: item.materialType, quantityKg: Number(item.quantityKg), estimatedValue: item.estimatedValueInr, status: item.status, owner: 'household'});
  const localRequest = item => item && ({id: item.id, status: item.status, quantityKg: Object.values(item.quantityByType || {}).reduce((sum, value) => sum + Number(value), 0), quantityByType: item.quantityByType || {}, materialIds: [], area: item.region || 'Delhi', region: item.region || 'Delhi', regionId: item.regionId, assignedKabadiwalaId: item.assignedKabadiwalaId});
  async function refreshHousehold() {
    const [inventory, request, metrics] = await Promise.all([api(`/api/households/${householdId}/inventory`), api(`/api/households/${householdId}/collection-request`), api(`/api/households/${householdId}/metrics`)]);
    state.materials = inventory.inventory.map(localMaterial);
    state.requests = request.request ? [localRequest(request.request)] : [];
    render();
    window.phirPaintMetrics?.([`${metrics.totalRecordedKg} kg`, `${metrics.totalCollectedKg} kg`, `₹${metrics.estimatedValueInr}`, `${metrics.collectionsCompleted}`]);
    const region = request.request?.region;
    const heading = document.querySelector('.collection-section .section-heading');
    if (region && heading && !heading.querySelector('.household-region')) {
      const badge = document.createElement('span');
      badge.className = 'badge household-region';
      badge.textContent = `Region · ${region}`;
      heading.append(badge);
    }
  }
  async function run(action, success) {
    try { await action(); await refreshHousehold(); if (modal.open) modal.close(); toast(success); }
    catch (error) { if (modal.open && $('#form-error', modal)) $('#form-error', modal).textContent = error.message; else toast(error.message); }
  }
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-action]');
    if (!button || view !== 'household') return;
    const action = button.dataset.action;
    if (action === 'request-collection') {
      event.preventDefault(); event.stopImmediatePropagation();
      run(() => api('/api/collection-requests', {method: 'POST', body: JSON.stringify({householdId})}), 'Collection request created.');
    } else if (action === 'delete-confirmed') {
      event.preventDefault(); event.stopImmediatePropagation();
      run(() => api(`/api/materials/${button.dataset.id}`, {method: 'DELETE'}), 'Material removed.');
    }
  }, true);
  document.addEventListener('submit', event => {
    const form = event.target;
    if (view !== 'household' || form.id !== 'material-form') return;
    event.preventDefault(); event.stopImmediatePropagation();
    const data = new FormData(form), id = form.dataset.id;
    if (form.dataset.photo === 'true') {
      const file = $('#material-photo')?.files?.[0];
      if (!file) { $('#form-error', modal).textContent = 'Choose a JPG or PNG photo first.'; return; }
      run(async () => {
        let result;
        try {
          const upload = await api('/api/image-upload', {method: 'POST', body: JSON.stringify({filename: file.name, contentType: file.type})});
          const uploaded = await fetch(upload.uploadUrl, {method: 'PUT', headers: {'Content-Type': file.type, 'x-amz-server-side-encryption': 'AES256'}, body: file});
          if (!uploaded.ok) throw new Error(`Image upload failed (${uploaded.status}).`);
          result = await api('/api/classify-image', {method: 'POST', body: JSON.stringify({s3Key: upload.key})});
        } catch (uploadError) {
          result = await api('/api/classify-image', {method: 'POST', body: JSON.stringify({filename: file.name})});
        }
        const detection = result.detections?.[0];
        if (!detection) throw new Error('No recyclable material was detected.');
        const materialType = detection.materialType === 'other' ? data.get('type') : detection.materialType;
        await api('/api/materials', {method: 'POST', body: JSON.stringify({userId: householdId, materialType, quantityKg: Number(data.get('weight'))})});
      }, 'Material identified and saved.');
      return;
    }
    const payload = {userId: householdId, materialType: data.get('type'), quantityKg: Number(data.get('weight'))};
    run(() => api(id ? `/api/materials/${id}` : '/api/materials', {method: id ? 'PUT' : 'POST', body: JSON.stringify(payload)}), 'Material saved.');
  }, true);
  const originalGo = go;
  go = function(next) { originalGo(next); if (next === 'household') refreshHousehold().catch(error => toast(error.message)); };
  if (view === 'household') refreshHousehold().catch(error => toast(error.message));
})();
