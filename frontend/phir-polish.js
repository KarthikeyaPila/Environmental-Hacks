/* Small presentation polish shared by the live role workspaces. */
(() => {
  const style = document.createElement('style');
  style.textContent = `
    .phir-live-status{position:fixed;right:18px;bottom:18px;z-index:80;display:flex;align-items:center;gap:8px;padding:9px 13px;border:1px solid #24216b33;border-radius:22px;background:#fff1ca;color:#24216b;font-size:11px;box-shadow:0 6px 22px #24216b1c;opacity:0;transform:translateY(8px);transition:opacity .2s,transform .2s;pointer-events:none}
    .phir-live-status.visible{opacity:1;transform:none}
    .phir-live-status:before{content:'';width:8px;height:8px;border-radius:50%;background:#007e65;box-shadow:0 0 0 4px #007e6520}
    .phir-live-status.busy:before{background:#d08b18;box-shadow:0 0 0 4px #d08b1820;animation:phir-pulse 1s infinite}
    @keyframes phir-pulse{50%{opacity:.35}}
    @media(max-width:700px){.phir-live-status{right:10px;bottom:10px}.workspace-content,.workspace-main{padding-left:16px!important;padding-right:16px!important}.map-layout,.two-col,.profile-grid{grid-template-columns:1fr!important}.table-scroll{overflow-x:auto}.topbar{padding-left:16px!important;padding-right:16px!important}}
  `;
  document.head.append(style);
  const status = document.createElement('div');
  status.className = 'phir-live-status';
  status.textContent = 'Live recovery records';
  status.setAttribute('role', 'status');
  document.body.append(status);
  let timer;
  window.phirLiveStatus = (message, busy = false) => {
    clearTimeout(timer);
    status.textContent = message;
    status.classList.toggle('busy', busy);
    status.classList.add('visible');
    if (!busy) timer = setTimeout(() => status.classList.remove('visible'), 2600);
  };
  window.phirPaintMetrics = values => document.querySelectorAll('.metrics .metric-value').forEach((node, index) => { if (values[index] !== undefined) node.textContent = values[index]; });
  const originalFetch = window.fetch;
  window.fetch = async (...args) => {
    const request = args[0];
    const url = typeof request === 'string' ? request : request?.url || '';
    if (!url.includes('/api/')) return originalFetch(...args);
    window.phirLiveStatus('Updating recovery records…', true);
    try {
      const response = await originalFetch(...args);
      window.phirLiveStatus(response.ok ? 'Recovery records updated' : 'Recovery service returned an error');
      return response;
    } catch (error) {
      window.phirLiveStatus('Recovery service unavailable');
      throw error;
    }
  };
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-action="restart-confirmed"]');
    if (!button) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    fetch(`${window.PHIR_API_BASE || ''}/api/demo/reset`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'})
      .then(response => { if (!response.ok) throw new Error('Could not reset the demo data.'); return response.json(); })
      .then(() => { window.phirLiveStatus('Demo data reset'); window.location.hash = 'choose'; window.location.reload(); })
      .catch(error => window.phirLiveStatus(error.message));
  }, true);
})();
