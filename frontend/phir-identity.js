/* Lightweight demo identity layer.
 * This is deliberately not authentication: it selects one seeded profile so
 * every workspace reads and writes the same database owner consistently.
 */
(() => {
  const STORAGE_KEY = 'phir-demo-identities';
  const defaults = {household: 'household_1', kabadiwala: 'kabadiwala_1', recycler: 'recycler_1'};
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
    .phir-identity-card select{width:100%;min-height:46px;padding:10px 12px;border:1px solid #202363;border-radius:8px;background:#fffdf4;color:#202363}
    .phir-identity-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:22px}.phir-account-button{white-space:nowrap}
  `;
  document.head.append(style);

  let usersPromise;
  const loadUsers = () => usersPromise ||= fetch(`${window.PHIR_API_BASE || ''}/api/demo/users`).then(response => response.json()).then(body => body.users || []);
  const close = () => document.querySelector('.phir-identity-dialog')?.remove();
  async function openPicker(forceRole) {
    const role = forceRole || roleForView();
    if (!role) return;
    close();
    const users = (await loadUsers()).filter(user => user.role === role);
    const dialog = document.createElement('div');
    dialog.className = 'phir-identity-dialog';
    dialog.innerHTML = `<form class="phir-identity-card"><h2>Choose a demo account</h2><p>Select the ${role === 'kabadiwala' ? 'collection partner' : role} profile to use for this workspace. Changes are saved to the demo database.</p><label for="phir-demo-user">Profile</label><select id="phir-demo-user" required>${users.map(user => `<option value="${user.id}">${user.name} · ${user.id}</option>`).join('')}</select><div class="phir-identity-actions"><button type="button" class="btn secondary" data-cancel>Cancel</button><button class="btn" type="submit">Continue</button></div></form>`;
    document.body.append(dialog);
    dialog.querySelector('[data-cancel]').onclick = close;
    dialog.addEventListener('click', event => { if (event.target === dialog) close(); });
    dialog.querySelector('form').onsubmit = event => {
      event.preventDefault();
      const profile = users.find(user => user.id === dialog.querySelector('select').value);
      if (!profile) return;
      identity.set(role, profile);
      location.reload();
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
    button.textContent = `Account · ${identity.profileFor(role).name}`;
    if (!sessionStorage.getItem(`phir-account-seen:${role}`)) {
      sessionStorage.setItem(`phir-account-seen:${role}`, 'true');
      setTimeout(() => openPicker(role), 250);
    }
  }
  new MutationObserver(install).observe(document.querySelector('#app') || document.body, {childList: true, subtree: true});
  setTimeout(install, 0);
})();
