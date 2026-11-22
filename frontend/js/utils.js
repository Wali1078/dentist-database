/* ── Toast ───────────────────────────────────────────────────────────────── */
function toast(msg, type = 'success') {
  const c = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = msg;
  c.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

/* ── Modal ───────────────────────────────────────────────────────────────── */
function openModal(html) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.innerHTML = `<div class="modal">${html}</div>`;
  overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
  return overlay;
}
function closeModal() {
  const m = document.querySelector('.modal-overlay');
  if (m) m.remove();
}

/* ── Confirm dialog ──────────────────────────────────────────────────────── */
function confirmDialog(msg) {
  return new Promise(resolve => {
    const html = `
      <div class="modal-header"><h2>تأیید</h2></div>
      <p style="margin-bottom:1.25rem">${msg}</p>
      <div class="modal-footer">
        <button class="btn btn-danger" id="conf-yes">بله، ادامه دهید</button>
        <button class="btn btn-outline" id="conf-no">لغو</button>
      </div>`;
    const ov = openModal(html);
    ov.querySelector('#conf-yes').onclick = () => { ov.remove(); resolve(true); };
    ov.querySelector('#conf-no').onclick  = () => { ov.remove(); resolve(false); };
  });
}

/* ── Misc ────────────────────────────────────────────────────────────────── */
function fmtMoney(n) {
  if (n == null) return '—';
  return new Intl.NumberFormat('fa-AF').format(Number(n)) + ' ؋';
}

function statusBadge(status) {
  const map = {
    'نوبت‌دار':     'badge-blue',
    'تکمیل شده':  'badge-green',
    'لغو شده':    'badge-red',
    'غایب':       'badge-yellow',
    'پرداخت شده': 'badge-green',
    'قسمی':       'badge-yellow',
    'پرداخت نشده':'badge-red',
  };
  const cls = map[status] || 'badge-gray';
  return `<span class="badge ${cls}">${status}</span>`;
}

function escHtml(s) {
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function getFormData(form) {
  const fd = new FormData(form);
  const obj = {};
  for (const [k, v] of fd.entries()) {
    obj[k] = v === '' ? null : v;
  }
  return obj;
}

function renderEmpty(msg = 'هیچ موردی یافت نشد') {
  return `<div class="empty-state">
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
    <p>${msg}</p>
  </div>`;
}
