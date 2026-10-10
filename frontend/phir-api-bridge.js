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
  const fileAsBase64 = file => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
  const localMaterial = item => ({id: item.id, type: item.materialType, quantityKg: Number(item.quantityKg), estimatedValue: item.estimatedValueInr, status: item.status || 'available', owner: 'household'});
  const localRequest = item => item && ({id: item.id, status: item.status, quantityKg: Object.values(item.quantityByType || {}).reduce((sum, value) => sum + Number(value), 0), quantityByType: item.quantityByType || {}, materialIds: [], area: item.region || 'Delhi', region: item.region || 'Delhi', regionId: item.regionId, assignedKabadiwalaId: item.assignedKabadiwalaId});
  async function refreshHousehold() {
    const [inventory, request, metrics] = await Promise.all([api(`/api/households/${householdId}/inventory`), api(`/api/households/${householdId}/collection-request`), api(`/api/households/${householdId}/metrics`)]);
    state.materials = inventory.inventory.map(localMaterial);
    state.requests = request.request ? [localRequest(request.request)] : [];
    // A background refresh must not tear down an active modal. In particular,
    // selecting a photo can outlive the initial household refresh and render()
    // would otherwise close the dialog while recognition is in progress.
    if (!modal.open) render();
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
    document.querySelectorAll('button[type="submit"]').forEach(button => { button.disabled = true; button.dataset.busy = 'true'; });
    try { await action(); await refreshHousehold(); if (modal.open) modal.close(); toast(success); }
    catch (error) { if (modal.open && $('#form-error', modal)) $('#form-error', modal).textContent = error.message; else toast(error.message); }
    finally { document.querySelectorAll('button[data-busy="true"]').forEach(button => { button.disabled = false; delete button.dataset.busy; }); }
  }
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-action]');
    if (!button || view !== 'household') return;
    const action = button.dataset.action;
    if (action === 'photo-material') {
      // The explicit submit action is the confirmation; the extra checkbox
      // adds friction and can block the form through native required-field
      // validation. Remove it after the modal is opened by the main UI.
      setTimeout(() => modal.querySelector('.confirm-material')?.remove(), 0);
    } else if (action === 'request-collection') {
      event.preventDefault(); event.stopImmediatePropagation();
      run(() => api('/api/collection-requests', {method: 'POST', body: JSON.stringify({householdId})}), 'Collection request created.');
    } else if (action === 'delete-confirmed') {
      event.preventDefault(); event.stopImmediatePropagation();
      run(() => api(`/api/materials/${button.dataset.id}`, {method: 'DELETE'}), 'Material removed.');
    }
  }, true);
  document.addEventListener('change', event => {
    if (event.target.id !== 'material-photo' || view !== 'household') return;
    const file = event.target.files?.[0], form = event.target.closest('form');
    if (!file || !form) return;
    (async () => {
      const message = form.querySelector('#form-error');
      try {
        const preview = form.querySelector('#photo-preview');
        if (preview) { preview.src = URL.createObjectURL(file); preview.hidden = false; }
        const resultTitle = form.querySelector('#photo-result-title');
        const resultCopy = form.querySelector('#photo-result-copy');
        if (resultTitle) resultTitle.textContent = 'Analyzing your photo…';
        if (resultCopy) resultCopy.textContent = 'Checking for one dominant recyclable material.';
        if (message) { message.className = 'note'; message.textContent = ''; }
        const upload = await api('/api/image-upload', {method: 'POST', body: JSON.stringify({filename: file.name, contentType: file.type})});
        const uploaded = await fetch(upload.uploadUrl, {method: 'PUT', headers: {'Content-Type': file.type, 'x-amz-server-side-encryption': 'AES256'}, body: file});
        if (!uploaded.ok) throw new Error(`Image upload failed (${uploaded.status}).`);
        const result = await api('/api/classify-image', {method: 'POST', body: JSON.stringify({s3Key: upload.key})});
        const detection = result.detections?.[0];
        if (!detection) throw new Error('No recyclable material was detected.');
        form.dataset.classification = JSON.stringify({fileName: file.name, fileSize: file.size, detection});
        const type = detection.materialType;
        form.dataset.recommendedType = type;
        const select = form.querySelector('#material-type');
        if (select && [...select.options].some(option => option.value === type)) select.value = type;
        const confidence = Math.round(Number(detection.confidence || 0) * 100);
        if (resultTitle) resultTitle.textContent = `We think this is ${type}.`;
        if (resultCopy) resultCopy.textContent = `${confidence}% confidence · Review the material and confirm below.`;
        const submit = form.querySelector('#material-submit');
        if (submit) submit.innerHTML = `${icon('check')} Confirm ${type} · add material`;
      } catch (error) {
        const resultTitle = form.querySelector('#photo-result-title');
        const resultCopy = form.querySelector('#photo-result-copy');
        if (resultTitle) resultTitle.textContent = 'We could not identify this photo.';
        if (resultCopy) resultCopy.textContent = 'Choose the material manually, then confirm below.';
        if (message) { message.className = 'error-message'; message.textContent = `Recognition failed: ${error.message}`; }
      }
    })();
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
        const cached = JSON.parse(form.dataset.classification || 'null');
        if (cached?.fileName === file.name && cached.fileSize === file.size && cached.detection) {
          result = {detections: [cached.detection]};
        } else {
          try {
            const upload = await api('/api/image-upload', {method: 'POST', body: JSON.stringify({filename: file.name, contentType: file.type})});
            const uploaded = await fetch(upload.uploadUrl, {method: 'PUT', headers: {'Content-Type': file.type, 'x-amz-server-side-encryption': 'AES256'}, body: file});
            if (!uploaded.ok) throw new Error(`Image upload failed (${uploaded.status}).`);
            result = await api('/api/classify-image', {method: 'POST', body: JSON.stringify({s3Key: upload.key})});
          } catch (uploadError) {
            result = await api('/api/classify-image', {method: 'POST', body: JSON.stringify({filename: file.name, imageBase64: await fileAsBase64(file)})});
          }
        }
        const detection = result.detections?.[0];
        if (!detection) throw new Error('No recyclable material was detected.');
        const materialType = detection.materialType === 'other' ? data.get('type') : detection.materialType;
        const materialSelect = form.querySelector('#material-type');
        if (materialSelect && [...materialSelect.options].some(option => option.value === materialType)) materialSelect.value = materialType;
        const recommendation = form.querySelector('#form-error');
        if (recommendation) {
          recommendation.className = 'note';
          recommendation.textContent = `Recommended: ${materialType} (${Math.round(Number(detection.confidence || 0) * 100)}% confidence).`;
        }
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
