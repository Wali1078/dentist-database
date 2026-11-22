let _invoices = [];

async function initBilling() {
  await loadInvoices();
}

async function loadInvoices(patientId = '') {
  const el = document.getElementById('page-billing');
  const url = patientId ? `/api/billing?patient_id=${patientId}` : '/api/billing';
  try {
    _invoices = await api.get(url);
    renderInvoices(el, _invoices);
  } catch(e) {
    el.innerHTML = `<div class="card"><p class="text-danger">${escHtml(e.message)}</p></div>`;
  }
}

function renderInvoices(el, list) {
  el.innerHTML = `
    <div class="section-header">
      <h2>صورت‌حساب‌ها (${list.length})</h2>
      <button class="btn btn-primary btn-sm" onclick="openInvoiceForm()">+ صورت‌حساب جدید</button>
    </div>
    ${list.length === 0 ? renderEmpty('هیچ صورت‌حسابی یافت نشد') : `
    <div class="card table-wrap">
      <table>
        <thead><tr>
          <th>#</th><th>بیمار</th><th>تاریخ</th><th>مبلغ کل</th><th>تخفیف</th><th>خالص</th><th>پرداخت شده</th><th>مانده</th><th>وضعیت</th><th>عملیات</th>
        </tr></thead>
        <tbody>
          ${list.map((inv, i) => `<tr>
            <td>${inv.id}</td>
            <td>${inv.patient_id}</td>
            <td>${escHtml(inv.invoice_date)}</td>
            <td>${fmtMoney(inv.total_amount)}</td>
            <td>${fmtMoney(inv.discount_amount)}</td>
            <td><strong>${fmtMoney(inv.net_amount)}</strong></td>
            <td class="text-success">${fmtMoney(inv.amount_paid)}</td>
            <td class="${parseFloat(inv.balance_due)>0?'text-danger':'text-success'}">${fmtMoney(inv.balance_due)}</td>
            <td>${statusBadge(inv.status)}</td>
            <td style="white-space:nowrap">
              <button class="btn btn-primary btn-sm" onclick="openPaymentForm(${inv.id}, ${inv.balance_due})">پرداخت</button>
              <button class="btn btn-danger btn-sm" onclick="deleteInvoice(${inv.id})">حذف</button>
            </td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>`}`;
}

function openInvoiceForm() {
  const html = `
    <div class="modal-header"><h2>صورت‌حساب جدید</h2><button class="btn" onclick="closeModal()">✕</button></div>
    <form id="inv-form" onsubmit="saveInvoice(event)">
      <div class="form-row">
        <div class="form-group"><label>شناسه بیمار *</label><input name="patient_id" type="number" required></div>
        <div class="form-group"><label>تاریخ (شمسی)</label><input name="invoice_date" placeholder="1403-01-15"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>مبلغ کل (؋) *</label><input name="total_amount" type="number" step="0.01" required></div>
        <div class="form-group"><label>تخفیف (؋)</label><input name="discount_amount" type="number" step="0.01" value="0"></div>
      </div>
      <div class="form-group"><label>دلیل تخفیف</label><input name="discount_reason"></div>
      <div class="form-group"><label>یادداشت</label><textarea name="notes" rows="2"></textarea></div>
      <div class="modal-footer">
        <button type="submit" class="btn btn-primary">ذخیره</button>
        <button type="button" class="btn btn-outline" onclick="closeModal()">لغو</button>
      </div>
    </form>`;
  openModal(html);
}

async function saveInvoice(e) {
  e.preventDefault();
  const data = getFormData(e.target);
  data.patient_id = parseInt(data.patient_id);
  data.total_amount = parseFloat(data.total_amount);
  data.discount_amount = parseFloat(data.discount_amount || 0);
  try {
    await api.post('/api/billing', data);
    closeModal();
    toast('صورت‌حساب ثبت شد');
    await loadInvoices();
  } catch(err) { toast(err.message, 'error'); }
}

function openPaymentForm(invoiceId, balance) {
  const html = `
    <div class="modal-header"><h2>ثبت پرداخت</h2><button class="btn" onclick="closeModal()">✕</button></div>
    <p class="text-muted" style="margin-bottom:1rem">مانده: <strong>${fmtMoney(balance)}</strong></p>
    <form id="pay-form" onsubmit="savePayment(event, ${invoiceId})">
      <div class="form-group"><label>مبلغ (؋) *</label><input name="amount" type="number" step="0.01" required max="${balance}"></div>
      <div class="form-group"><label>تاریخ پرداخت (شمسی)</label><input name="payment_date" placeholder="1403-01-15"></div>
      <div class="form-group"><label>یادداشت</label><input name="note"></div>
      <div class="modal-footer">
        <button type="submit" class="btn btn-primary">ثبت پرداخت</button>
        <button type="button" class="btn btn-outline" onclick="closeModal()">لغو</button>
      </div>
    </form>`;
  openModal(html);
}

async function savePayment(e, invoiceId) {
  e.preventDefault();
  const data = getFormData(e.target);
  data.invoice_id = invoiceId;
  data.amount = parseFloat(data.amount);
  try {
    const r = await api.post('/api/billing/payments', data);
    closeModal();
    toast(`پرداخت ثبت شد — وضعیت: ${r.invoice_status}`);
    await loadInvoices();
  } catch(err) { toast(err.message, 'error'); }
}

async function deleteInvoice(id) {
  const ok = await confirmDialog('آیا می‌خواهید این صورت‌حساب را حذف کنید؟');
  if (!ok) return;
  try {
    await api.delete(`/api/billing/${id}`);
    toast('صورت‌حساب حذف شد');
    await loadInvoices();
  } catch(err) { toast(err.message, 'error'); }
}
