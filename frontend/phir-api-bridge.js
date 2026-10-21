/* Backend bridge for the primary Phir frontend. */
(() => {
  const API_BASE = window.PHIR_API_BASE || '';
  let householdId = window.phirIdentity?.idFor('household') || 'household_1';
  let householdHydrated = false;
  let householdRevision = 0;
  let householdRefreshSequence = 0;
  const api = async (path, options = {}) => {
    const url = `${API_BASE}${path}`;
    if ((options.method || 'GET').toUpperCase() === 'GET' && window.phirApiRead) return window.phirApiRead(url);
    const response = await fetch(`${API_BASE}${path}`, {
      headers: {'Content-Type': 'application/json', ...(options.headers || {})},
      ...options,
    });
    const body = await response.json();
    if (!response.ok) {
      const message = body?.error?.message || 'The recovery service is unavailable.';
      if (response.status === 404 && message === 'household profile not found' && window.phirIdentity) {
        window.phirIdentity.reset('household');
        sessionStorage.removeItem('phir-account-seen:household');
        const next = new URL(location.href);
        next.searchParams.delete('profile');
        next.searchParams.delete('profileRole');
        location.replace(next.toString());
      }
      throw new Error(message);
    }
    window.phirApiInvalidate?.('/api/');
    return body;
  };
  const localMaterial = item => ({id: item.id, type: item.materialType, quantityKg: Number(item.quantityKg), estimatedValue: item.estimatedValueInr, status: item.status || 'available', owner: 'household'});
  const localRequest = item => item && ({id: item.id, status: item.status, quantityKg: Object.values(item.quantityByType || {}).reduce((sum, value) => sum + Number(value), 0), quantityByType: item.quantityByType || {}, materialIds: [], area: item.region || 'Delhi', region: item.region || 'Delhi', regionId: item.regionId, assignedKabadiwalaId: item.assignedKabadiwalaId});
  function groupHouseholdMaterials() {
    if (view !== 'household') return;
    if (!document.getElementById('household-material-groups-style')) {
      const style = document.createElement('style');
      style.id = 'household-material-groups-style';
      style.textContent = '.workspace[data-theme="household"] .material-group-count{display:inline-block;margin-left:6px;color:var(--muted);font-size:10px;font-weight:600;white-space:nowrap}.workspace[data-theme="household"] .material-details h3{display:flex;align-items:baseline;flex-wrap:wrap;gap:2px}';
      document.head.append(style);
    }
    const workspace = document.querySelector('.workspace[data-theme="household"]');
    const grid = workspace?.querySelector('#workspace-content .materials-grid');
    if (!grid) return;
    const cards = [...grid.querySelectorAll(':scope > .material-card')];
    // The source template renders one card per inventory record, in the same
    // order as state.materials. If a different template is present, leave it
    // untouched rather than risk pairing a card with the wrong record.
    if (cards.length !== state.materials.length) return;
    const displayNames = {pet: 'pet plastic', cardboard: 'cardboard', paper: 'paper', aluminium: 'aluminium', glass: 'glass', wood: 'wood'};
    const aligned = cards.every((card, index) => {
      const title = card.querySelector('.material-details h3')?.textContent.trim().toLowerCase();
      const status = card.querySelector('.material-image .badge')?.textContent.trim().toLowerCase();
      const record = state.materials[index];
      return title === displayNames[record?.type] && status === String(record?.status || '').toLowerCase();
    });
    if (!aligned) return;
    const groups = new Map();
    state.materials.forEach((material, index) => {
      const key = `${material.type}|${material.status}`;
      if (!groups.has(key)) groups.set(key, {type: material.type, status: material.status, records: [], cards: []});
      const group = groups.get(key);
      group.records.push(material);
      group.cards.push(cards[index]);
    });
    for (const group of groups.values()) {
      const card = group.cards[0];
      const ids = group.records.map(record => record.id).filter(Boolean);
      const weight = group.records.reduce((sum, record) => sum + Number(record.quantityKg || 0), 0);
      const hasAllQuotes = group.records.every(record => record.estimatedValue != null && Number.isFinite(Number(record.estimatedValue)));
      const value = hasAllQuotes ? group.records.reduce((sum, record) => sum + Number(record.estimatedValue), 0) : null;
      const label = group.type === 'pet' ? 'PET plastic' : group.type ? `${group.type[0].toUpperCase()}${group.type.slice(1)}` : 'material';
      const badge = card.querySelector('.material-image .badge');
      if (badge) badge.textContent = group.status;
      const values = card.querySelectorAll('.material-row span');
      if (values[0]) values[0].textContent = `${new Intl.NumberFormat('en-IN', {maximumFractionDigits: 1}).format(weight)} kg`;
      if (values[1]) values[1].textContent = value == null ? 'Quote pending' : `₹${new Intl.NumberFormat('en-IN').format(value)}`;
      const title = card.querySelector('.material-details h3');
      if (title) {
        title.textContent = label;
        if (group.records.length > 1) {
          const count = document.createElement('small');
          count.className = 'material-group-count';
          count.textContent = `${group.records.length} entries`;
          title.append(' ', count);
        }
      }
      const actions = card.querySelector('.material-actions');
      if (actions) {
        actions.querySelectorAll('[data-action="edit-material"]').forEach(button => {
          if (group.records.length > 1) button.remove();
        });
        const remove = actions.querySelector('[data-action="delete-material"]');
        if (remove) {
          remove.dataset.materialIds = encodeURIComponent(JSON.stringify(ids));
          remove.dataset.materialLabel = label;
          remove.dataset.materialCount = String(group.records.length);
          remove.setAttribute('aria-label', group.records.length > 1 ? `Delete all ${group.records.length} ${label} entries` : `Delete ${label}`);
          remove.title = group.records.length > 1 ? `Delete all ${group.records.length} ${label} entries` : `Delete ${label}`;
        }
      }
      group.cards.slice(1).forEach(duplicate => duplicate.remove());
    }
    const countLabel = workspace.querySelector('#workspace-content .section-heading small');
    if (countLabel?.textContent.includes('recorded materials')) {
      const recordCount = state.materials.length;
      countLabel.textContent = `${groups.size} material groups · ${recordCount} records`;
    }
  }
  function requestGroupDelete(ids, label, count) {
    const safeLabel = String(label || 'material').replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
    const encodedIds = encodeURIComponent(JSON.stringify(ids));
    openModal(`Remove ${count > 1 ? 'material group' : 'material'}?`, `<p style="font-size:13px">${count > 1 ? `This removes all ${count} ${safeLabel} entries in this slot.` : `This removes this ${safeLabel} entry.`} This cannot be undone.</p><div class="modal-actions"><button class="btn secondary" data-action="close-modal">Cancel</button><button class="btn" data-action="delete-confirmed" data-material-ids="${encodedIds}" data-material-count="${count}">Remove ${count > 1 ? `all ${count} entries` : 'material'}</button></div>`);
  }
  function polishHouseholdLayout() {
    if (view !== 'household') return;
    const layout = document.querySelector('.workspace[data-theme="household"] .two-col');
    const materials = layout?.querySelector(':scope > section');
    const collection = materials?.querySelector('.collection-section');
    if (layout && materials && collection && !layout.querySelector('.household-collection-panel')) {
      const panel = document.createElement('aside');
      panel.className = 'household-collection-panel';
      panel.append(collection);
      layout.append(panel);
    }
    layout?.querySelector(':scope > aside:not(.household-collection-panel)')?.remove();
    const manual = document.querySelector('.workspace .dashboard-identify [data-action="add-material"]');
    if (manual) manual.textContent = 'Add materials manually';
    document.querySelectorAll('.workspace .metric-label').forEach(label => {
      if (label.textContent.trim() === 'Estimated value · sample') label.textContent = 'Estimated recovery value';
    });
    document.querySelector('.workspace[data-theme="household"] .dashboard-functional-title [data-action="add-material"]')?.remove();
    document.querySelector('.workspace[data-theme="household"] .dashboard-partners')?.remove();
    polishCollectionProgress();
  }
  function polishCollectionProgress() {
    const section = document.querySelector('.workspace[data-theme="household"] .collection-section');
    const request = state.requests.at(-1);
    if (!section || !request) return;
    if (!document.getElementById('household-progress-style')) {
      const style = document.createElement('style');
      style.id = 'household-progress-style';
      style.textContent = '.collection-section .progress-kicker{display:block;margin:0 0 5px;color:var(--primary);font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}.collection-section .status-line{align-items:center;gap:10px;margin:18px 0 22px}.collection-section .status-line .status-dot{width:9px;height:9px;box-shadow:0 0 0 5px color-mix(in srgb,var(--primary) 15%,transparent)}.collection-section .collection-status-copy{font-weight:700}.collection-section .steps{gap:10px;margin:0 0 24px}.collection-section .step{min-height:48px;padding-top:11px;font-size:11px}.collection-section .step.current{color:var(--primary);font-weight:800}.collection-section .processing-note{margin:0;font-size:12px;line-height:1.6}';
      document.head.append(style);
    }
    const heading = section.querySelector('.section-heading h2');
    if (heading) heading.textContent = 'Collection progress';
    const headingWrap = section.querySelector('.section-heading');
    if (headingWrap && !headingWrap.querySelector('.progress-kicker')) {
      const kicker = document.createElement('span');
      kicker.className = 'progress-kicker';
      kicker.textContent = 'Processing stage';
      headingWrap.prepend(kicker);
      headingWrap.style.alignItems = 'flex-start';
      headingWrap.style.flexDirection = 'column';
      headingWrap.style.gap = '3px';
    }
    const copy = request.status === 'pending'
      ? 'Step 1 of 3 · Your request is waiting for a collection partner to accept it.'
      : request.status === 'accepted'
        ? 'Step 2 of 3 · A collection partner accepted your request. Please keep the material ready for handover.'
        : 'Step 3 of 3 · Collection completed. The material has moved into the recovery network.';
    const statusLine = section.querySelector('.status-line');
    if (statusLine) statusLine.innerHTML = `<span class="status-dot"></span><span class="collection-status-copy">${copy}</span><span class="badge">${kg(request.quantityKg)}</span>`;
    const labels = ['Request sent', 'Partner accepted', 'Collected'];
    section.querySelectorAll('.step').forEach((step, index) => {
      step.textContent = labels[index] || step.textContent;
      step.classList.toggle('current', (request.status === 'pending' && index === 0) || (request.status === 'accepted' && index === 1) || (request.status === 'collected' && index === 2));
    });
    const note = section.querySelector('p.muted');
    if (note) note.remove();
  }
  async function refreshHousehold() {
    householdId = window.phirIdentity?.idFor('household') || householdId;
    const revision = householdRevision;
    const sequence = ++householdRefreshSequence;
    const [inventory, request, metrics] = await Promise.all([api(`/api/households/${householdId}/inventory`), api(`/api/households/${householdId}/collection-request`), api(`/api/households/${householdId}/metrics`)]);
    if (revision !== householdRevision || sequence !== householdRefreshSequence) return;
    state.materials = inventory.inventory.map(localMaterial);
    state.requests = request.request ? [localRequest(request.request)] : [];
    householdHydrated = true;
    // A background refresh must not tear down an active modal. In particular,
    // selecting a photo can outlive the initial household refresh and render()
    // would otherwise close the dialog while recognition is in progress.
    if (!modal.open) render();
    window.phirMarkWorkspaceReady?.();
    polishHouseholdLayout();
    setTimeout(polishHouseholdLayout, 0);
    window.phirPaintMetrics?.([`${metrics.totalRecordedKg} kg`, `${metrics.totalCollectedKg} kg`, `₹${metrics.estimatedValueInr}`, `${metrics.collectionsCompleted}`]);
    groupHouseholdMaterials();
    setTimeout(groupHouseholdMaterials, 0);
    const region = request.request?.region;
    const heading = document.querySelector('.collection-section .section-heading');
    if (region && heading && !heading.querySelector('.household-region')) {
      const badge = document.createElement('span');
      badge.className = 'badge household-region';
      badge.textContent = `Region · ${region}`;
      heading.append(badge);
    }
  }
  function optimisticMaterial(type, quantityKg, id) {
    const previousIndex = state.materials.findIndex(item => item.id === id);
    const previous = previousIndex >= 0 ? {...state.materials[previousIndex]} : null;
    const material = {id: id || `pending-${Date.now()}`, type, quantityKg, estimatedValue: Math.round(quantityKg * ({pet:25,cardboard:12,paper:15,aluminium:100,glass:5,wood:0}[type] || 0)), status: id ? (state.materials.find(item => item.id === id)?.status || 'available') : 'available', owner: 'household'};
    const existing = state.materials.findIndex(item => item.id === id);
    if (existing >= 0) state.materials[existing] = material;
    else state.materials.unshift(material);
    render();
    return {
      rollback() {
        if (previous) {
          const currentIndex = state.materials.findIndex(item => item.id === id);
          if (currentIndex >= 0) state.materials[currentIndex] = previous;
          else state.materials.splice(Math.min(previousIndex, state.materials.length), 0, previous);
        } else state.materials = state.materials.filter(item => item.id !== material.id);
        render();
      },
      update(nextType, nextQuantityKg = material.quantityKg) {
        material.type = nextType;
        material.quantityKg = Number(nextQuantityKg);
        material.estimatedValue = Math.round(material.quantityKg * ({pet:25,cardboard:12,paper:15,aluminium:100,glass:5,wood:0}[nextType] || 0));
        state.materials = state.materials.map(item => item.id === material.id ? {...material} : item);
        render();
      },
      commit(saved) { if (!saved?.id) return; state.materials = state.materials.map(item => item.id === material.id ? localMaterial(saved) : item); render(); },
    };
  }
  function run(action, success, optimistic) {
    // Close first and keep the local change visible while persistence happens
    // independently. A slow API must not hold the user in the dialog.
    if (modal.open) modal.close();
    window.phirLiveStatus?.('Saving your change…', true);
    Promise.resolve().then(action).then(result => {
      householdRevision += 1;
      optimistic?.commit?.(result);
      render();
      toast(success);
      window.phirLiveStatus?.('Saved to recovery records');
      refreshHousehold().catch(error => console.warn('Background household refresh failed:', error));
    }).catch(error => {
      householdRevision += 1;
      optimistic?.rollback?.();
      render();
      toast(`Could not save: ${error.message}`);
      refreshHousehold().catch(refreshError => console.warn('Household rollback refresh failed:', refreshError));
    });
  }
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-action]');
    if (!button || view !== 'household') return;
    const action = button.dataset.action;
    if (action === 'add-material') {
      event.preventDefault(); event.stopImmediatePropagation();
      openModal('Add material', `<p class="modal-intro">Choose how you want to record your recyclable material.</p><div class="modal-choice-grid"><button class="btn" type="button" data-action="add-material-manual">Add manually</button><button class="btn secondary" type="button" data-action="photo-material">Get a demo suggestion from a photo</button></div>`);
    } else if (action === 'add-material-manual') {
      event.preventDefault(); event.stopImmediatePropagation();
      materialForm();
    } else if (action === 'photo-material') {
      // The explicit submit action is the confirmation; the extra checkbox
      // adds friction and can block the form through native required-field
      // validation. Remove it after the modal is opened by the main UI.
      setTimeout(() => modal.querySelector('.confirm-material')?.remove(), 0);
    } else if (action === 'request-collection') {
      event.preventDefault(); event.stopImmediatePropagation();
      householdRevision += 1;
      const selected = state.materials.filter(item => item.status === 'available');
      const requestedBefore = selected.map(item => ({id: item.id, status: item.status}));
      const previousRequests = state.requests.slice();
      const preview = {id: `pending-${Date.now()}`, status: 'pending', quantityKg: selected.reduce((sum, item) => sum + Number(item.quantityKg || 0), 0), area: window.phirIdentity?.profileFor('household')?.locality || 'Delhi'};
      state.materials = state.materials.map(item => item.status === 'available' ? {...item, status: 'requested'} : item);
      state.requests = [...state.requests.filter(item => item.status !== 'pending' && item.status !== 'accepted'), preview];
      render();
      run(() => api('/api/collection-requests', {method: 'POST', body: JSON.stringify({householdId})}), 'Collection request created.', {
        commit(saved) { state.requests = state.requests.map(item => item.id === preview.id ? localRequest(saved) : item); render(); },
        rollback() {
          requestedBefore.forEach(item => { const current = state.materials.find(material => material.id === item.id); if (current) current.status = item.status; });
          state.requests = [...state.requests.filter(item => item.id !== preview.id), ...previousRequests];
          render();
        },
      });
    } else if (action === 'delete-material') {
      event.preventDefault(); event.stopImmediatePropagation();
      let ids = [];
      try { ids = JSON.parse(decodeURIComponent(button.dataset.materialIds || '')); } catch {}
      if (!ids.length && button.dataset.id) ids = [button.dataset.id];
      const records = ids.map(id => state.materials.find(item => item.id === id)).filter(Boolean);
      if (!records.length || records.some(item => item.status !== 'available')) {
        toast('Only available materials can be removed.');
        return;
      }
      requestGroupDelete(ids, button.dataset.materialLabel || records[0].type, records.length);
    } else if (action === 'delete-confirmed') {
      event.preventDefault(); event.stopImmediatePropagation();
      householdRevision += 1;
      let ids = [];
      try { ids = JSON.parse(decodeURIComponent(button.dataset.materialIds || '')); } catch {}
      if (!ids.length && button.dataset.id) ids = [button.dataset.id];
      const before = state.materials.map((item, index) => ({item: {...item}, index})).filter(entry => ids.includes(entry.item.id));
      if (!before.length) { modal.close(); toast('This material group is no longer in your inventory.'); return; }
      const selected = new Set(ids);
      state.materials = state.materials.filter(item => !selected.has(item.id));
      modal.close();
      render();
      window.phirLiveStatus?.('Removing material group…', true);
      Promise.allSettled(ids.map(id => api(`/api/materials/${id}`, {method: 'DELETE', body: JSON.stringify({userId: householdId})}))).then(results => {
        const failedIds = ids.filter((_, index) => results[index].status === 'rejected');
        const failed = new Set(failedIds);
        for (const entry of before.filter(({item}) => failed.has(item.id)).sort((a, b) => a.index - b.index)) {
          if (!state.materials.some(item => item.id === entry.item.id)) state.materials.splice(Math.min(entry.index, state.materials.length), 0, entry.item);
        }
        render();
        const removed = ids.length - failedIds.length;
        if (removed && failedIds.length) toast(`Removed ${removed}; ${failedIds.length} could not be removed. Inventory refreshed.`);
        else if (removed) toast(removed > 1 ? `Removed all ${removed} entries.` : 'Material removed.');
        else toast('Could not remove this material group. Your inventory was restored.');
        window.phirLiveStatus?.(failedIds.length ? 'Inventory needs a refresh' : 'Saved to recovery records');
        refreshHousehold().catch(error => console.warn('Inventory refresh after removal failed:', error));
      });
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
        if (resultTitle) resultTitle.textContent = 'Preparing a demo suggestion…';
        if (resultCopy) resultCopy.textContent = 'This demo does not analyze or upload the photo.';
        if (message) { message.className = 'note'; message.textContent = ''; }
        const result = await api('/api/classify-image', {method: 'POST', body: JSON.stringify({filename: file.name})});
        const detection = result.detections?.[0];
        if (!detection) throw new Error('No demo suggestion was available.');
        form.dataset.classification = JSON.stringify({fileName: file.name, fileSize: file.size, detection, mode: result.mode});
        const type = detection.materialType;
        form.dataset.recommendedType = type;
        const select = form.querySelector('#material-type');
        if (select && [...select.options].some(option => option.value === type)) select.value = type;
        if (resultTitle) resultTitle.textContent = `Demo suggestion: ${type}.`;
        if (resultCopy) resultCopy.textContent = 'Simulated from the filename only; no image analysis ran. Review or change the material before confirming.';
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
      householdRevision += 1;
      const quantityKg = Number(data.get('weight'));
      const optimistic = optimisticMaterial(data.get('type'), quantityKg);
      run(async () => {
        let result;
        const cached = JSON.parse(form.dataset.classification || 'null');
        if (cached?.fileName === file.name && cached.fileSize === file.size && cached.detection) {
          result = {detections: [cached.detection], mode: cached.mode};
        } else {
          result = await api('/api/classify-image', {method: 'POST', body: JSON.stringify({filename: file.name})});
        }
        const detection = result.detections?.[0];
        if (!detection) throw new Error('No demo suggestion was available.');
        const materialType = detection.materialType === 'other' ? data.get('type') : detection.materialType;
        const materialSelect = form.querySelector('#material-type');
        if (materialSelect && [...materialSelect.options].some(option => option.value === materialType)) materialSelect.value = materialType;
        const recommendation = form.querySelector('#form-error');
        if (recommendation) {
          recommendation.className = 'note';
          recommendation.textContent = `Demo suggestion: ${materialType} (simulated; no image analysis).`;
        }
        optimistic.update(materialType, quantityKg);
        return api('/api/materials', {method: 'POST', body: JSON.stringify({userId: householdId, materialType, quantityKg})});
      }, 'Demo suggestion saved. Please confirm materials manually.', optimistic);
      return;
    }
    const payload = {userId: householdId, materialType: data.get('type'), quantityKg: Number(data.get('weight'))};
    householdRevision += 1;
    const optimistic = optimisticMaterial(payload.materialType, payload.quantityKg, id);
    run(() => api(id ? `/api/materials/${id}` : '/api/materials', {method: id ? 'PUT' : 'POST', body: JSON.stringify(payload)}), 'Material saved.', optimistic);
  }, true);
  const originalGo = go;
  const originalRender = render;
  render = function() {
    // The legacy renderer scrolls to the top on every render. Household
    // optimistic updates replace the workspace DOM, so preserve the current
    // position for in-place updates while still starting role navigation at
    // the top of its new page.
    const keepPosition = Boolean(document.querySelector('.workspace[data-theme="household"]'));
    const scrollTop = window.scrollY;
    originalRender();
    if (keepPosition) window.scrollTo(0, scrollTop);
    // Tab changes replace the workspace markup, so restore the ready state
    // after every render instead of showing the workspace loading overlay.
    if (view === 'household') window.phirMarkWorkspaceReady?.();
    if (view === 'household') {
      polishHouseholdLayout();
      groupHouseholdMaterials();
      setTimeout(() => { polishHouseholdLayout(); groupHouseholdMaterials(); }, 0);
    }
  };
  go = function(next) { originalGo(next); if (next === 'household') refreshHousehold().catch(error => toast(error.message)); };
  window.phirRefreshHousehold = () => refreshHousehold().catch(error => toast(error.message));
  window.addEventListener('phir-profile-updated', event => { if (event.detail?.role === 'household') window.phirRefreshHousehold(); });
  document.addEventListener('click', event => {
    const tabButton = event.target.closest?.('.workspace[data-theme="household"] .tab');
    if (tabButton?.textContent.trim() === 'Contributions' && !householdHydrated) {
      refreshHousehold().catch(error => toast(error.message));
    }
  });
  if (view === 'household') refreshHousehold().catch(error => toast(error.message));
  function warmHouseholdOnChooser() {
    if (view !== 'select') return;
    const profile = window.phirIdentity?.profileFor('household');
    if (!profile?.id) return;
    for (const resource of ['inventory', 'collection-request', 'metrics', 'profile']) {
      window.phirApiWarm?.(`/api/households/${profile.id}/${resource}`);
    }
  }
  new MutationObserver(warmHouseholdOnChooser).observe(document.querySelector('#app') || document.body, {childList: true, subtree: true});
  warmHouseholdOnChooser();
})();
