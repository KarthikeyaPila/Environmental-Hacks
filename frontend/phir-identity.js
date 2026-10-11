/* Lightweight demo identity layer. This is deliberately not authentication. */
(() => {
  const STORAGE_KEY = 'phir-demo-identities';
  const defaults = {household: 'household_1', kabadiwala: 'kabadiwala_1', recycler: 'recycler_1'};
  const areas = ['North', 'North West', 'West', 'South West', 'Central', 'New Delhi', 'North East', 'Shahdara', 'East', 'South East', 'South'];
  const safe = value => String(value ?? '').replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
  let selected = {};
  try { selected = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') || {}; } catch (_) { selected = {}; }

  const roleForView = () => {
    const theme = document.querySelector('.workspace')?.dataset.theme;
    return ({household: 'household', collector: 'kabadiwala', recycler: 'recycler'}[theme] || null);
  };
  const identity = {
    idFor(role) { return selected[role]?.id || defaults[role]; },
    profileFor(role) { return selected[role] || {id: defaults[role], name: 'Demo account'}; },
    set(role, profile) {
      selected[role] = {id: profile.id, name: profile.name, role: profile.role};
      localStorage.setItem(STORAGE_KEY, JSON.stringify(selected));
    },
  };
  window.phirIdentity = identity;

  const style = document.createElement('style');
  style.textContent = `
    .phir-identity-dialog{position:fixed;inset:0;z-index:10000;display:grid;place-items:center;padding:20px;background:rgba(25,28,45,.42)}
    .phir-identity-card{width:min(520px,100%);padding:28px;border:2px solid #202363;border-radius:18px;background:#fff9e9;box-shadow:7px 7px 0 #ffdc38;color:#202363}
    .phir-identity-card h2{margin:0 0 8px;color:#cf1f3d}.phir-identity-card p{margin:0 0 20px}.phir-identity-card label{display:block;margin:0 0 8px;font-weight:700;font-size:13px}
    .phir-identity-card input,.phir-identity-card select{width:100%;min-height:46px;margin:0 0 16px;padding:10px 12px;border:1px solid #202363;border-radius:8px;background:#fffdf4;color:#202363}
    .phir-identity-card .phir-identity-error{margin:0 0 12px;color:#cf1f3d;font-weight:700}
    .phir-identity-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:22px}.phir-account-button{white-space:nowrap}
  `;
  document.head.append(style);

  const close = () => document.querySelector('.phir-identity-dialog')?.remove();
  async function openPicker(forceRole) {
    const role = forceRole || roleForView();
    if (!role) return;
    close();
    const current = identity.profileFor(role);
    const label = role === 'kabadiwala' ? 'collection partner' : role;
    const currentArea = current.locality || areas[0];
    const dialog = document.createElement('div');
    dialog.className = 'phir-identity-dialog';
    dialog.innerHTML = `<form class="phir-identity-card"><h2>Your ${safe(label)} profile</h2><p>Enter a name and choose the Delhi area ${role === 'kabadiwala' ? 'you serve' : 'you live in'}. This creates a lightweight demo profile—no password required.</p><label for="phir-demo-name">Name</label><input id="phir-demo-name" name="name" required maxlength="80" value="${safe(current.name === 'Demo account' ? '' : current.name || '')}" placeholder="e.g. Asha Verma"><label for="phir-demo-area">${role === 'kabadiwala' ? 'Service area' : 'Area'}</label><select id="phir-demo-area" name="locality" required>${areas.map(area => `<option ${area === currentArea ? 'selected' : ''}>${area}</option>`).join('')}</select><div class="phir-identity-actions"><button type="button" class="btn secondary" data-cancel>Cancel</button><button class="btn" type="submit">Continue</button></div></form>`;
    document.body.append(dialog);
    dialog.querySelector('[data-cancel]').onclick = close;
    dialog.addEventListener('click', event => { if (event.target === dialog) close(); });
    dialog.querySelector('form').onsubmit = event => {
      event.preventDefault();
      const form = dialog.querySelector('form');
      const submit = form.querySelector('button[type="submit"]');
      submit.disabled = true;
      fetch(`${window.PHIR_API_BASE || ''}/api/demo/profiles`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({id: current.id, role, name: form.name.value.trim(), locality: form.locality.value})})
        .then(response => response.json().then(body => ({response, body})))
        .then(({response, body}) => { if (!response.ok) throw new Error(body?.error?.message || 'Could not save profile.'); identity.set(role, body); location.reload(); })
        .catch(error => { submit.disabled = false; const message = document.createElement('p'); message.className = 'phir-identity-error'; message.textContent = error.message; form.prepend(message); });
    };
  }
  window.phirOpenIdentityPicker = openPicker;

  function install() {
    const role = roleForView();
    const links = document.querySelector('#app .workspace .top-links');
    if (!role || !links) return;
    let button = links.querySelector('.phir-account-button');
    if (!button) {
      button = document.createElement('button');
      button.type = 'button';
      button.className = 'text-link phir-account-button';
      button.onclick = () => openPicker(role);
      links.append(button);
    }
    const label = `Account · ${identity.profileFor(role).name}`;
    if (button.textContent !== label) button.textContent = label;
    if (!sessionStorage.getItem(`phir-account-seen:${role}`)) {
      sessionStorage.setItem(`phir-account-seen:${role}`, 'true');
      setTimeout(() => openPicker(role), 250);
    }
  }
  new MutationObserver(install).observe(document.querySelector('#app') || document.body, {childList: true, subtree: true});
  setTimeout(install, 0);
})();
