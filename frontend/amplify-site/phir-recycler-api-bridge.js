/* Backend bridge for the recycler workspace. */
(() => {
  const API_BASE = window.PHIR_API_BASE || '';
  let recyclerId = window.phirIdentity?.idFor('recycler') || 'recycler_1';
  let hasOwnProfile = Boolean(window.phirIdentity?.profileFor('recycler')?.id);
  const recyclerAreas = ['North', 'North West', 'West', 'South West', 'Central', 'New Delhi', 'North East', 'Shahdara', 'East', 'South East', 'South'];
  let recyclerRevision = 0;
  let recyclerRefreshSequence = 0;
  const api = async (path, options = {}) => {
    const url = `${API_BASE}${path}`;
    if ((options.method || 'GET').toUpperCase() === 'GET' && window.phirApiRead) return window.phirApiRead(url);
    const response = await fetch(`${API_BASE}${path}`, {headers: {'Content-Type': 'application/json', ...(options.headers || {})}, ...options});
    const body = await response.json();
    if (!response.ok) throw new Error(body?.error?.message || 'The recovery service is unavailable.');
    window.phirApiInvalidate?.('/api/');
    return body;
  };
  const localRequirement = item => ({id: item.id, type: item.materialType, quantityKg: Number(item.requiredQuantityKg), minimumKg: Number(item.minimumQuantityKg || 0), fulfilledKg: Number(item.fulfilledQuantityKg || 0), company: state.company.name, status: item.status});
  const localBooking = item => ({id: item.id, type: item.materialType, quantityKg: Number(item.quantityKg), partner: item.kabadiwalaId, requirementId: item.requirementId, status: item.status === 'confirmed' ? 'confirmed' : item.status === 'completed' ? 'completed' : item.status});
  const materialLabel = value => String(value || '').replaceAll('_', ' ').replace(/\b\w/g, letter => letter.toUpperCase());
  function hydrateMarketplace() {
    document.querySelectorAll('.lot-card').forEach((card, index) => {
      const lot = state.lots[index];
      if (!lot) return;
      const top = card.querySelector('.lot-top');
      if (top && !top.querySelector('.data-origin-badge')) {
        const badge = document.createElement('span');
        badge.className = 'badge data-origin-badge';
        badge.textContent = lot.isDemo ? 'Demo' : 'Real';
        top.prepend(badge);
      }
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
      if (note.textContent.includes('Sample records for the presentation') || note.textContent.includes('Added material has no live quote') || note.textContent.includes('Collection and transfer are recorded separately')) note.remove();
    });
    if (!document.getElementById('recycler-requirement-style')) {
      const style = document.createElement('style');
      style.id = 'recycler-requirement-style';
      style.textContent = '.workspace[data-theme="recycler"] #workspace-content{visibility:visible!important}.workspace[data-theme="recycler"] #workspace-content:after{display:none!important}.workspace[data-theme="recycler"] .requirement-row{display:grid;grid-template-columns:minmax(220px,1fr) minmax(220px,1.2fr) auto;gap:26px;align-items:center;padding:22px 24px;margin:0 0 14px;border:2px solid var(--primary);border-radius:14px;background:var(--surface);box-shadow:4px 4px 0 color-mix(in srgb,var(--secondary) 70%,transparent)}.workspace[data-theme="recycler"] .requirement-row h3{font-size:24px;margin:5px 0 7px}.workspace[data-theme="recycler"] .requirement-row .eyebrow{color:var(--primary);font-weight:800}.workspace[data-theme="recycler"] .requirement-row .progressbar{height:9px;border-radius:99px;background:color-mix(in srgb,var(--line) 70%,transparent);overflow:hidden;margin-top:10px}.workspace[data-theme="recycler"] .requirement-row .progressbar span{border-radius:99px}.workspace[data-theme="recycler"] .requirement-row>.badge{justify-self:end}.recycler-data-banner{margin:0 0 20px;padding:12px 16px;border-left:4px solid var(--cyan);background:color-mix(in srgb,var(--cyan) 10%,var(--surface));color:var(--ink);font-size:14px}.recycler-setup-hint{margin:12px 0;color:var(--ink)}@media(max-width:700px){.workspace[data-theme="recycler"] .requirement-row{grid-template-columns:1fr}.workspace[data-theme="recycler"] .requirement-row>.badge{justify-self:start}}';
      document.head.append(style);
    }
    const workspace = document.querySelector('#workspace-content');
    if (workspace && !hasOwnProfile) {
      let banner = workspace.querySelector('.recycler-data-banner');
      if (!banner) { banner = document.createElement('aside'); banner.className = 'recycler-data-banner'; workspace.prepend(banner); }
      const bannerText = tab === 'Company profile'
        ? 'Create your company profile to get started. The seeded recycler accounts and their records are demo data.'
        : 'Demo preview · This is a shared sample recycler account. Create your profile before publishing requirements, booking material or confirming handovers.';
      if (banner.textContent !== bannerText) banner.textContent = bannerText;
    } else workspace?.querySelector('.recycler-data-banner')?.remove();
    if (tab === 'Company profile') {
      const form = document.getElementById('company-form');
      const locality = form?.querySelector('[name="locality"]');
      if (locality && locality.tagName !== 'SELECT') {
        const current = hasOwnProfile ? state.company.locality || '' : '';
        const select = document.createElement('select');
        select.id = locality.id;
        select.name = locality.name;
        select.required = true;
        if (!hasOwnProfile) {
          const placeholder = document.createElement('option');
          placeholder.value = '';
          placeholder.textContent = 'Choose a Delhi locality';
          placeholder.selected = true;
          placeholder.disabled = true;
          select.append(placeholder);
        }
        for (const areaName of [...recyclerAreas, ...(current && !recyclerAreas.includes(current) ? [current] : [])]) {
          const option = document.createElement('option');
          option.value = areaName;
          option.textContent = areaName;
          option.selected = areaName === current;
          select.append(option);
        }
        locality.replaceWith(select);
      }
      const name = form?.querySelector('[name="name"]');
      const contact = form?.querySelector('[name="contact"]');
      if (!hasOwnProfile) {
        if (name && name.value !== '') name.value = '';
        if (contact && contact.value !== '') contact.value = '';
      }
      const submit = form?.querySelector('[type="submit"]');
      const submitText = hasOwnProfile ? 'Save company profile' : 'Create company profile';
      if (submit && submit.textContent !== submitText) submit.textContent = submitText;
      const note = form?.querySelector('.note');
      if (note) {
        note.classList.add('recycler-setup-hint');
        const noteText = hasOwnProfile
          ? 'Your profile is saved in the recovery database. This lightweight profile is not a secure login.'
          : 'Your profile gets its own requirements and bookings. No password or separate login is needed.';
        if (note.textContent !== noteText) note.textContent = noteText;
      }
    }
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
    recyclerId = window.phirIdentity?.idFor('recycler') || recyclerId;
    hasOwnProfile = Boolean(window.phirIdentity?.profileFor('recycler')?.id);
    const revision = recyclerRevision;
    const sequence = ++recyclerRefreshSequence;
    const [requirements, available, bookings, metrics, profile] = await Promise.all([
      api(`/api/recyclers/${recyclerId}/requirements`),
      api(`/api/recyclers/${recyclerId}/available-material`),
      api(`/api/recyclers/${recyclerId}/bookings`),
      api(`/api/recyclers/${recyclerId}/metrics`),
      api(`/api/recyclers/${recyclerId}/profile`),
    ]);
    if (revision !== recyclerRevision || sequence !== recyclerRefreshSequence) return;
    state.company = {name: profile.name, locality: profile.locality, contact: profile.contact || '', isDemo: Boolean(profile.isDemo)};
    state.requirements = requirements.requirements.map(localRequirement);
    state.lots = available.availableMaterial.map(item => ({id: `${item.kabadiwalaId}:${item.materialType}`, type: item.materialType, quantityKg: Number(item.quantityKg), partner: item.kabadiwalaName || item.kabadiwalaId, area: item.region || 'Delhi', regionId: item.regionId, isDemo: Boolean(item.isDemo), status: 'collected'}));
    state.bookings = bookings.bookings.map(localBooking);
    render();
    window.phirMarkWorkspaceReady?.();
    [0, 100, 500].forEach(delay => setTimeout(() => { polishRecyclerView(); hydrateMarketplace(); }, delay));
    window.phirPaintMetrics?.([`${metrics.reservedBookings}`, `${metrics.fulfilledQuantityKg} kg`, `${metrics.completedBookings}`, `${metrics.requirements.length}`]);
  }
  function run(action, success, optimistic) {
    recyclerRevision += 1;
    optimistic?.apply?.();
    if (modal.open) modal.close();
    if (optimistic) render();
    window.phirLiveStatus?.('Saving your change…', true);
    Promise.resolve().then(action).then(result => {
      recyclerRevision += 1;
      optimistic?.commit?.(result);
      if (optimistic) render();
      toast(success);
      window.phirLiveStatus?.('Saved to recovery records');
      refreshRecycler().catch(error => console.warn('Background recycler refresh failed:', error));
    }).catch(error => {
      recyclerRevision += 1;
      optimistic?.rollback?.();
      if (optimistic) render();
      toast(`Could not save: ${error.message}`);
      refreshRecycler().catch(refreshError => console.warn('Recycler rollback refresh failed:', refreshError));
    });
  }
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-action]');
    if (!button || view !== 'recycler') return;
    const action = button.dataset.action;
    if (!hasOwnProfile && ['add-requirement', 'reserve', 'confirm-booking'].includes(action)) {
      event.preventDefault(); event.stopImmediatePropagation();
      tab = 'Company profile'; render();
      toast('Create your company profile before making changes to the shared demo data.');
      return;
    }
    if (action === 'confirm-booking') {
      event.preventDefault(); event.stopImmediatePropagation();
      const booking = state.bookings.find(item => item.id === button.dataset.id);
      const requirement = booking && state.requirements.find(item => item.id === booking.requirementId);
      const previousBooking = booking && {...booking};
      const previousRequirement = requirement && {...requirement};
      const optimistic = booking ? {apply() {
        booking.status = 'completed';
        if (requirement) { requirement.fulfilledKg = Math.min(requirement.quantityKg, requirement.fulfilledKg + booking.quantityKg); requirement.status = requirement.fulfilledKg >= requirement.quantityKg ? 'fulfilled' : 'partially_fulfilled'; }
      }, rollback() {
        Object.assign(booking, previousBooking);
        if (requirement) Object.assign(requirement, previousRequirement);
      }} : null;
      run(() => api(`/api/bookings/${button.dataset.id}/confirm`, {method: 'POST', body: JSON.stringify({recyclerId})}), 'Handover recorded.', optimistic);
    }
  }, true);
  document.addEventListener('submit', event => {
    const form = event.target;
    if (view !== 'recycler') return;
    if (!hasOwnProfile && ['requirement-form', 'booking-form'].includes(form.id)) {
      event.preventDefault(); event.stopImmediatePropagation();
      if (modal.open) modal.close();
      tab = 'Company profile'; render();
      toast('Create your company profile before making changes to the shared demo data.');
      return;
    }
    if (form.id === 'requirement-form') {
      event.preventDefault(); event.stopImmediatePropagation();
      const data = new FormData(form);
      const draft = {id:`pending-${Date.now()}`,type:data.get('type'),quantityKg:Number(data.get('weight')),minimumKg:Number(data.get('minimum')||0),fulfilledKg:0,company:state.company.name,status:'open'};
      run(() => api('/api/recycler-requirements', {method: 'POST', body: JSON.stringify({recyclerId, materialType: data.get('type'), requiredQuantityKg: Number(data.get('weight')), minimumQuantityKg: Number(data.get('minimum') || 0)})}), 'Requirement published.', {apply(){state.requirements.unshift(draft);},commit(saved){state.requirements=state.requirements.map(item=>item.id===draft.id?localRequirement(saved):item);},rollback(){state.requirements=state.requirements.filter(item=>item.id!==draft.id);}});
    } else if (form.id === 'company-form') {
      event.preventDefault(); event.stopImmediatePropagation();
      const data = new FormData(form);
      const profile = {name:String(data.get('name') || '').trim(),locality:String(data.get('locality') || ''),contact:String(data.get('contact') || '').trim()};
      if (!profile.name || !profile.locality) { toast('Enter a company name and choose a locality.'); return; }
      if (!hasOwnProfile) {
        const submit = form.querySelector('[type="submit"]');
        if (submit) { submit.disabled = true; submit.textContent = 'Creating your profile…'; }
        api('/api/demo/profiles', {method: 'POST', body: JSON.stringify({role: 'recycler', ...profile})})
          .then(created => {
            window.phirIdentity?.set('recycler', created);
            const next = new URL(location.href);
            next.searchParams.set('profile', created.id);
            next.searchParams.set('profileRole', 'recycler');
            history.replaceState(history.state, '', next.toString());
            recyclerId = created.id;
            hasOwnProfile = true;
            render();
            refreshRecycler().catch(error => toast(error.message));
            window.phirLiveStatus?.('Company profile ready');
          })
          .catch(error => {
            if (submit) { submit.disabled = false; submit.textContent = 'Create company profile'; }
            toast(`Could not create profile: ${error.message}`);
          });
        return;
      }
      const previous = {...state.company};
      run(() => api(`/api/recyclers/${recyclerId}/profile`, {method: 'POST', body: JSON.stringify({recyclerId, ...profile})}), 'Company profile saved.', {apply(){state.company=profile;},rollback(){state.company=previous;}});
    } else if (form.id === 'booking-form') {
      event.preventDefault(); event.stopImmediatePropagation();
      const data = new FormData(form), [kabadiwalaId, materialType] = String(form.dataset.id).split(':');
      const lot = state.lots.find(item => item.id === form.dataset.id);
      const quantityKg = Number(data.get('quantity'));
      const requirement = state.requirements.find(item => item.id === data.get('requirement'));
      const previousLot = lot && {...lot};
      const previousRequirement = requirement && {...requirement};
      const draft = {id:`pending-${Date.now()}`,type:lot?.type,quantityKg,partner:lot?.partner,requirementId:data.get('requirement'),status:'confirmed'};
      run(() => api('/api/bookings', {method: 'POST', body: JSON.stringify({recyclerId, requirementId: data.get('requirement'), kabadiwalaId, quantityKg})}), 'Material reserved.', {apply(){
        if (lot) { lot.quantityKg = Math.max(0, lot.quantityKg - quantityKg); if (lot.quantityKg <= 0.001) state.lots = state.lots.filter(item => item.id !== lot.id); }
        if (requirement) requirement.fulfilledKg = Math.min(requirement.quantityKg, requirement.fulfilledKg + quantityKg);
        state.bookings.unshift(draft);
      },commit(saved){state.bookings=state.bookings.map(item=>item.id===draft.id?localBooking(saved):item);},rollback(){
        state.bookings=state.bookings.filter(item=>item.id!==draft.id);
        if (previousLot) {
          const currentLot=state.lots.find(item=>item.id===previousLot.id);
          if (currentLot) Object.assign(currentLot,previousLot);
          else state.lots.push(previousLot);
        }
        if (previousRequirement) {
          const currentRequirement=state.requirements.find(item=>item.id===previousRequirement.id);
          if (currentRequirement) Object.assign(currentRequirement,previousRequirement);
        }
      }});
    }
  }, true);
  const originalGo = go;
  const originalRender = render;
  render = function() {
    originalRender();
    if (view === 'recycler') {
      window.phirMarkWorkspaceReady?.();
      polishRecyclerView();
      setTimeout(polishRecyclerView, 0);
    }
  };
  go = function(next) { if (next === 'recycler' && !hasOwnProfile) tab = 'Company profile'; originalGo(next); };
  window.addEventListener('phir-profile-updated', event => { if (event.detail?.role === 'recycler') { recyclerId = event.detail.profile.id; hasOwnProfile = true; refreshRecycler().catch(error => toast(error.message)); } });
  window.addEventListener('hashchange', () => {
    if (view !== 'recycler') return;
    if (!hasOwnProfile && tab !== 'Company profile') { tab = 'Company profile'; render(); }
    refreshRecycler().catch(error => toast(error.message));
  });
  if (view === 'recycler' && !hasOwnProfile) { tab = 'Company profile'; render(); }
  if (view === 'recycler') refreshRecycler().catch(error => toast(error.message));
  // render() already invokes polishRecyclerView synchronously. Avoid observing
  // #app here: rewriting text nodes from a childList observer can retrigger it
  // forever and block the role-transition timer on slower devices.
  function warmRecyclerOnChooser() {
    if (view !== 'select') return;
    const profile = window.phirIdentity?.profileFor('recycler');
    if (!profile?.id) return;
    for (const resource of ['requirements', 'available-material', 'bookings', 'metrics', 'profile']) {
      window.phirApiWarm?.(`/api/recyclers/${profile.id}/${resource}`);
    }
  }
  new MutationObserver(warmRecyclerOnChooser).observe(document.querySelector('#app') || document.body, {childList: true, subtree: true});
  warmRecyclerOnChooser();
})();
