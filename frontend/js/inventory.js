let _inventory = [];

async function initInventory() {
  await loadInventory();
}

async function loadInventory(lowStock = false) {
  const el = document.getElementById('page-inventory');
  const url = lowStock ? '/api/inventory/low-stock' : '/api/inventory';
  try {
    _inventory = await api.get(url);
    renderInventory(el, _inventory, lowStock);
  } catch(e) {
    el.innerHTML = `<div class="card"><p class="text-danger">${escHtml(e.message)}</p></div>`;
  }
}

function renderInventory(el, list, lowStock) {
  el.innerHTML = `
    <div class="section-header">
      <h2>انبار مواد (${list.length})</h2>
      <div style="display:flex;gap:.5rem">
        <button class="btn btn-outline btn-sm ${lowStock?'active':''}" onclick="loadInventory(true)">کم‌موجود</button>
        <button class="btn btn-outline btn-sm ${!lowStock?'active':''}" onclick="loadInventory(false)">همه</button>
        <button class="btn btn-primary btn-sm" onclick="openItemForm()">+ ماده جدید</button>
      </div>
    </div>
    ${list.length === 0 ? renderEmpty('انبار خالی است') : `
    <div class="card table-wrap">
      <table>
        <thead><tr>
          <th>#</th><th>نام ماده</th><th>کتگوری</th><th>موجودی</th><th>حد سفارش</th><th>قیمت واحد</th><th>تامین کننده</th><th>وضعیت</th><th>عملیات</th>
        </tr></thead>
        <tbody>
          ${list.map((item, i) => {
            const low = parseFloat(item.quantity_in_stock) <= parseFloat(item.reorder_level);
            return `<tr>
              <td>${i+1}</td>
              <td><strong>${escHtml(item.item_name)}</strong></td>
              <td>${escHtml(item.category||'—')}</td>
              <td class="${low?'text-danger':'text-success'}">${item.quantity_in_stock} ${escHtml(item.unit_type)}</td>
              <td class="text-muted">${item.reorder_level}</td>
              <td>${fmtMoney(item.cost_per_unit)}</td>
              <td>${escHtml(item.supplier_name||'—')}</td>
              <td>${low ? '<span class="badge badge-red">کم‌موجود</span>' : '<span class="badge badge-green">کافی</span>'}</td>
              <td style="white-space:nowrap">
                <button class="btn btn-outline btn-sm" onclick="openItemForm(${item.id})">ویرایش</button>
                <button class="btn btn-danger btn-sm" onclick="deleteItem(${item.id})">حذف</button>
              </td>
            </tr>`;}).join('')}
        </tbody>
      </table>
    </div>`}`;
}

function openItemForm(id = null) {
  const item = id ? _inventory.find(x => x.id === id) : {};
  const title = id ? 'ویرایش ماده' : 'ماده جدید';
  const html = `
    <div class="modal-header"><h2>${title}</h2><button class="btn" onclick="closeModal()">✕</button></div>
    <form id="item-form" onsubmit="saveItem(event, ${id})">
      <div class="form-group"><label>نام ماده *</label><input name="item_name" required value="${escHtml(item.item_name||'')}"></div>
      <div class="form-row">
        <div class="form-group"><label>کتگوری</label><input name="category" value="${escHtml(item.category||'')}"></div>
        <div class="form-group"><label>واحد</label><input name="unit_type" value="${escHtml(item.unit_type||'عدد')}"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>موجودی</label><input name="quantity_in_stock" type="number" step="0.001" value="${item.quantity_in_stock||0}"></div>
        <div class="form-group"><label>حد سفارش مجدد</label><input name="reorder_level" type="number" step="0.001" value="${item.reorder_level||5}"></div>
      </div>
      <div class="form-group"><label>قیمت واحد (؋)</label><input name="cost_per_unit" type="number" step="0.01" value="${item.cost_per_unit||0}"></div>
      <div class="form-row">
        <div class="form-group"><label>تامین کننده</label><input name="supplier_name" value="${escHtml(item.supplier_name||'')}"></div>
        <div class="form-group"><label>تلفن تامین کننده</label><input name="supplier_phone" dir="ltr" value="${escHtml(item.supplier_phone||'')}"></div>
      </div>
      <div class="form-group"><label>تاریخ انقضا (شمسی)</label><input name="expiry_date" placeholder="1405-01-01" value="${escHtml(item.expiry_date||'')}"></div>
      <div class="modal-footer">
        <button type="submit" class="btn btn-primary">ذخیره</button>
        <button type="button" class="btn btn-outline" onclick="closeModal()">لغو</button>
      </div>
    </form>`;
  openModal(html);
}

async function saveItem(e, id) {
  e.preventDefault();
  const data = getFormData(e.target);
  data.quantity_in_stock = parseFloat(data.quantity_in_stock);
  data.reorder_level = parseFloat(data.reorder_level);
  data.cost_per_unit = parseFloat(data.cost_per_unit);
  try {
    if (id) await api.put(`/api/inventory/${id}`, data);
    else     await api.post('/api/inventory', data);
    closeModal();
    toast(id ? 'ماده بروزرسانی شد' : 'ماده ثبت شد');
    await loadInventory();
  } catch(err) { toast(err.message, 'error'); }
}

async function deleteItem(id) {
  const ok = await confirmDialog('آیا می‌خواهید این ماده را حذف کنید؟');
  if (!ok) return;
  try {
    await api.delete(`/api/inventory/${id}`);
    toast('ماده حذف شد');
    await loadInventory();
  } catch(err) { toast(err.message, 'error'); }
}
