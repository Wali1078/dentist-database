let _staff = [];

async function initStaff() {
  await loadStaff();
}

async function loadStaff(activeOnly = true) {
  const el = document.getElementById('page-staff');
  const url = activeOnly ? '/api/staff?active_only=true' : '/api/staff?active_only=false';
  try {
    _staff = await api.get(url);
    renderStaff(el, _staff, activeOnly);
  } catch(e) {
    el.innerHTML = `<div class="card"><p class="text-danger">${escHtml(e.message)}</p></div>`;
  }
}

function renderStaff(el, list, activeOnly) {
  el.innerHTML = `
    <div class="section-header">
      <h2>کارمندان (${list.length})</h2>
      <div style="display:flex;gap:.5rem">
        <button class="btn btn-outline btn-sm" onclick="loadStaff(false)">همه</button>
        <button class="btn btn-outline btn-sm" onclick="loadStaff(true)">فعال</button>
        <button class="btn btn-primary btn-sm" onclick="openStaffForm()">+ کارمند جدید</button>
      </div>
    </div>
    ${list.length === 0 ? renderEmpty('هیچ کارمندی یافت نشد') : `
    <div class="card table-wrap">
      <table>
        <thead><tr>
          <th>#</th><th>نام کامل</th><th>وظیفه</th><th>تخصص</th><th>تلفن</th><th>معاش (ماهانه)</th><th>وضعیت</th><th>عملیات</th>
        </tr></thead>
        <tbody>
          ${list.map((s, i) => `<tr>
            <td>${i+1}</td>
            <td><strong>${escHtml(s.full_name)}</strong></td>
            <td>${escHtml(s.role)}</td>
            <td>${escHtml(s.specialization||'—')}</td>
            <td dir="ltr">${escHtml(s.phone||'—')}</td>
            <td>${fmtMoney(s.monthly_salary)}</td>
            <td>${s.is_active ? '<span class="badge badge-green">فعال</span>' : '<span class="badge badge-gray">غیرفعال</span>'}</td>
            <td style="white-space:nowrap">
              <button class="btn btn-outline btn-sm" onclick="openStaffForm(${s.id})">ویرایش</button>
              <button class="btn btn-danger btn-sm" onclick="deleteStaff(${s.id})">حذف</button>
            </td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>`}`;
}

function openStaffForm(id = null) {
  const s = id ? _staff.find(x => x.id === id) : {};
  const title = id ? 'ویرایش کارمند' : 'کارمند جدید';
  const roles = ['دندانپزشک','نرس','منشی','مدیر','سایر'];
  const roleOpts = roles.map(r => `<option value="${r}" ${s.role===r?'selected':''}>${r}</option>`).join('');
  const html = `
    <div class="modal-header"><h2>${title}</h2><button class="btn" onclick="closeModal()">✕</button></div>
    <form id="staff-form" onsubmit="saveStaff(event, ${id})">
      <div class="form-row">
        <div class="form-group"><label>نام کامل *</label><input name="full_name" required value="${escHtml(s.full_name||'')}"></div>
        <div class="form-group"><label>وظیفه *</label><select name="role" required><option value="">انتخاب کنید</option>${roleOpts}</select></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>تخصص</label><input name="specialization" value="${escHtml(s.specialization||'')}"></div>
        <div class="form-group"><label>شماره جواز</label><input name="license_number" dir="ltr" value="${escHtml(s.license_number||'')}"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>شماره تلفن</label><input name="phone" dir="ltr" value="${escHtml(s.phone||'')}"></div>
        <div class="form-group"><label>معاش ماهانه (؋)</label><input name="monthly_salary" type="number" step="0.01" value="${s.monthly_salary||0}"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>ساعت شروع کار</label><input name="working_hours_start" placeholder="08:00" dir="ltr" value="${escHtml(s.working_hours_start||'')}"></div>
        <div class="form-group"><label>ساعت پایان کار</label><input name="working_hours_end" placeholder="17:00" dir="ltr" value="${escHtml(s.working_hours_end||'')}"></div>
      </div>
      <div class="form-group"><label>تاریخ استخدام (شمسی)</label><input name="hire_date" placeholder="1403-01-01" value="${escHtml(s.hire_date||'')}"></div>
      <div class="modal-footer">
        <button type="submit" class="btn btn-primary">ذخیره</button>
        <button type="button" class="btn btn-outline" onclick="closeModal()">لغو</button>
      </div>
    </form>`;
  openModal(html);
}

async function saveStaff(e, id) {
  e.preventDefault();
  const data = getFormData(e.target);
  data.monthly_salary = parseFloat(data.monthly_salary || 0);
  try {
    if (id) await api.put(`/api/staff/${id}`, data);
    else     await api.post('/api/staff', data);
    closeModal();
    toast(id ? 'کارمند بروزرسانی شد' : 'کارمند ثبت شد');
    await loadStaff();
  } catch(err) { toast(err.message, 'error'); }
}

async function deleteStaff(id) {
  const ok = await confirmDialog('آیا می‌خواهید این کارمند را حذف/غیرفعال کنید؟');
  if (!ok) return;
  try {
    const r = await api.delete(`/api/staff/${id}`);
    toast(r.message);
    await loadStaff();
  } catch(err) { toast(err.message, 'error'); }
}
