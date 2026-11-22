let _patients = [];

async function initPatients() {
  await loadPatients();
}

async function loadPatients(search = '') {
  const el = document.getElementById('page-patients');
  const url = search ? `/api/patients?search=${encodeURIComponent(search)}` : '/api/patients';
  try {
    _patients = await api.get(url);
    renderPatients(el, _patients, search);
  } catch(e) {
    el.innerHTML = `<div class="card"><p class="text-danger">${escHtml(e.message)}</p></div>`;
  }
}

function renderPatients(el, list, search) {
  el.innerHTML = `
    <div class="section-header">
      <h2>بیماران (${list.length})</h2>
      <button class="btn btn-primary btn-sm" onclick="openPatientForm()">+ بیمار جدید</button>
    </div>
    <div class="card" style="margin-bottom:1rem">
      <div class="search-bar">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input type="text" placeholder="جستجو بر اساس نام، شماره تلفن، تذکره..." value="${escHtml(search)}"
          oninput="loadPatients(this.value)" id="patient-search">
      </div>
    </div>
    ${list.length === 0 ? renderEmpty('هیچ بیماری ثبت نشده') : `
    <div class="card table-wrap">
      <table>
        <thead><tr>
          <th>#</th><th>نام کامل</th><th>جنسیت</th><th>تاریخ تولد</th><th>تلفن</th><th>ولایت</th><th>عملیات</th>
        </tr></thead>
        <tbody>
          ${list.map((p, i) => `<tr>
            <td>${i+1}</td>
            <td><strong>${escHtml(p.full_name)}</strong></td>
            <td>${escHtml(p.gender || '—')}</td>
            <td>${escHtml(p.date_of_birth || '—')}</td>
            <td dir="ltr">${escHtml(p.phone || '—')}</td>
            <td>${escHtml(p.province || '—')}</td>
            <td style="white-space:nowrap">
              <button class="btn btn-outline btn-sm" onclick="openPatientForm(${p.id})">ویرایش</button>
              <button class="btn btn-danger btn-sm" onclick="deletePatient(${p.id})">حذف</button>
            </td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>`}`;
}

function openPatientForm(id = null) {
  const p = id ? _patients.find(x => x.id === id) : {};
  const title = id ? 'ویرایش بیمار' : 'بیمار جدید';
  const html = `
    <div class="modal-header"><h2>${title}</h2><button class="btn" onclick="closeModal()">✕</button></div>
    <form id="patient-form" onsubmit="savePatient(event, ${id})">
      <div class="form-row">
        <div class="form-group"><label>نام کامل *</label><input name="full_name" required value="${escHtml(p.full_name||'')}"></div>
        <div class="form-group"><label>نام پدر</label><input name="father_name" value="${escHtml(p.father_name||'')}"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>جنسیت</label>
          <select name="gender">
            <option value="">—</option>
            <option value="مرد" ${p.gender==='مرد'?'selected':''}>مرد</option>
            <option value="زن"  ${p.gender==='زن' ?'selected':''}>زن</option>
          </select></div>
        <div class="form-group"><label>تاریخ تولد (شمسی)</label><input name="date_of_birth" placeholder="1370-06-15" value="${escHtml(p.date_of_birth||'')}"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>شماره تلفن</label><input name="phone" dir="ltr" value="${escHtml(p.phone||'')}"></div>
        <div class="form-group"><label>شماره تذکره</label><input name="tazkira_number" dir="ltr" value="${escHtml(p.tazkira_number||'')}"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>ولایت</label><input name="province" value="${escHtml(p.province||'')}"></div>
        <div class="form-group"><label>ولسوالی</label><input name="district" value="${escHtml(p.district||'')}"></div>
      </div>
      <div class="form-group"><label>آدرس</label><input name="address" value="${escHtml(p.address||'')}"></div>
      <div class="form-row">
        <div class="form-group"><label>مسلک</label><input name="occupation" value="${escHtml(p.occupation||'')}"></div>
        <div class="form-group"><label>حساسیت‌ها</label><input name="allergies" value="${escHtml(p.allergies||'')}"></div>
      </div>
      <div class="form-group"><label>یادداشت</label><textarea name="notes" rows="2">${escHtml(p.notes||'')}</textarea></div>
      <div class="modal-footer">
        <button type="submit" class="btn btn-primary">ذخیره</button>
        <button type="button" class="btn btn-outline" onclick="closeModal()">لغو</button>
      </div>
    </form>`;
  openModal(html);
}

async function savePatient(e, id) {
  e.preventDefault();
  const data = getFormData(e.target);
  try {
    if (id) await api.put(`/api/patients/${id}`, data);
    else     await api.post('/api/patients', data);
    closeModal();
    toast(id ? 'بیمار بروزرسانی شد' : 'بیمار ثبت شد');
    await loadPatients(document.getElementById('patient-search')?.value || '');
  } catch(err) {
    toast(err.message, 'error');
  }
}

async function deletePatient(id) {
  const ok = await confirmDialog('آیا می‌خواهید این بیمار را حذف کنید؟');
  if (!ok) return;
  try {
    const r = await api.delete(`/api/patients/${id}`);
    toast(r.message || 'بیمار حذف شد');
    await loadPatients();
  } catch(err) {
    toast(err.message, 'error');
  }
}
