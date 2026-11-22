let _expenses = [];

async function initExpenses() {
  await loadExpenses();
}

async function loadExpenses(category = '') {
  const el = document.getElementById('page-expenses');
  const url = category ? `/api/expenses?category=${encodeURIComponent(category)}` : '/api/expenses';
  try {
    _expenses = await api.get(url);
    renderExpenses(el, _expenses, category);
  } catch(e) {
    el.innerHTML = `<div class="card"><p class="text-danger">${escHtml(e.message)}</p></div>`;
  }
}

const EXPENSE_CATS = ['معاش','کرایه','برق','مواد','متفرقه'];

function renderExpenses(el, list, category) {
  const total = list.reduce((s, e) => s + parseFloat(e.amount||0), 0);
  const catOpts = ['', ...EXPENSE_CATS].map(c =>
    `<option value="${c}" ${c===category?'selected':''}>${c||'همه'}</option>`).join('');
  el.innerHTML = `
    <div class="section-header">
      <h2>مصارف (${list.length})</h2>
      <button class="btn btn-primary btn-sm" onclick="openExpenseForm()">+ مصرف جدید</button>
    </div>
    <div class="card" style="margin-bottom:1rem;display:flex;gap:1rem;align-items:center;flex-wrap:wrap">
      <label style="font-weight:600;font-size:.88rem">کتگوری:</label>
      <select style="width:160px" onchange="loadExpenses(this.value)">${catOpts}</select>
      <span class="text-muted" style="margin-right:auto">مجموع: <strong>${fmtMoney(total)}</strong></span>
    </div>
    ${list.length === 0 ? renderEmpty('هیچ مصرفی ثبت نشده') : `
    <div class="card table-wrap">
      <table>
        <thead><tr>
          <th>#</th><th>کتگوری</th><th>مبلغ</th><th>تاریخ</th><th>توضیح</th><th>عملیات</th>
        </tr></thead>
        <tbody>
          ${list.map((e, i) => `<tr>
            <td>${i+1}</td>
            <td><span class="badge badge-blue">${escHtml(e.category)}</span></td>
            <td><strong>${fmtMoney(e.amount)}</strong></td>
            <td>${escHtml(e.expense_date)}</td>
            <td class="text-muted">${escHtml(e.description||'—')}</td>
            <td style="white-space:nowrap">
              <button class="btn btn-danger btn-sm" onclick="deleteExpense(${e.id})">حذف</button>
            </td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>`}`;
}

function openExpenseForm() {
  const catOpts = EXPENSE_CATS.map(c => `<option value="${c}">${c}</option>`).join('');
  const html = `
    <div class="modal-header"><h2>مصرف جدید</h2><button class="btn" onclick="closeModal()">✕</button></div>
    <form id="exp-form" onsubmit="saveExpense(event)">
      <div class="form-row">
        <div class="form-group"><label>کتگوری *</label><select name="category" required>${catOpts}</select></div>
        <div class="form-group"><label>مبلغ (؋) *</label><input name="amount" type="number" step="0.01" required></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>تاریخ (شمسی)</label><input name="expense_date" placeholder="1403-01-15"></div>
        <div class="form-group"><label>شناسه کارمند</label><input name="staff_id" type="number"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>شناسه ماده انبار</label><input name="inventory_item_id" type="number"></div>
        <div class="form-group"><label>مقدار خریداری شده</label><input name="quantity_purchased" type="number" step="0.001"></div>
      </div>
      <div class="form-group"><label>توضیح</label><textarea name="description" rows="2"></textarea></div>
      <div class="modal-footer">
        <button type="submit" class="btn btn-primary">ذخیره</button>
        <button type="button" class="btn btn-outline" onclick="closeModal()">لغو</button>
      </div>
    </form>`;
  openModal(html);
}

async function saveExpense(e) {
  e.preventDefault();
  const data = getFormData(e.target);
  data.amount = parseFloat(data.amount);
  if (data.staff_id) data.staff_id = parseInt(data.staff_id);
  if (data.inventory_item_id) data.inventory_item_id = parseInt(data.inventory_item_id);
  if (data.quantity_purchased) data.quantity_purchased = parseFloat(data.quantity_purchased);
  try {
    await api.post('/api/expenses', data);
    closeModal();
    toast('مصرف ثبت شد');
    await loadExpenses();
  } catch(err) { toast(err.message, 'error'); }
}

async function deleteExpense(id) {
  const ok = await confirmDialog('آیا می‌خواهید این مصرف را حذف کنید؟');
  if (!ok) return;
  try {
    await api.delete(`/api/expenses/${id}`);
    toast('مصرف حذف شد');
    await loadExpenses();
  } catch(err) { toast(err.message, 'error'); }
}
