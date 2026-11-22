let _appointments = [];
let _apptDentists = [];

async function initAppointments() {
  _apptDentists = await api.get('/api/staff/dentists').catch(() => []);
  await loadAppointments();
}

async function loadAppointments(date = '') {
  const el = document.getElementById('page-appointments');
  const url = date ? `/api/appointments?date=${encodeURIComponent(date)}` : '/api/appointments/today';
  try {
    _appointments = await api.get(url);
    renderAppointments(el, _appointments, date);
  } catch(e) {
    el.innerHTML = `<div class="card"><p class="text-danger">${escHtml(e.message)}</p></div>`;
  }
}

function renderAppointments(el, list, date) {
  el.innerHTML = `
    <div class="section-header">
      <h2>نوبت‌ها</h2>
      <button class="btn btn-primary btn-sm" onclick="openApptForm()">+ نوبت جدید</button>
    </div>
    <div class="card" style="margin-bottom:1rem;display:flex;gap:1rem;align-items:center;flex-wrap:wrap">
      <label style="font-weight:600;font-size:.88rem">تاریخ (شمسی):</label>
      <input type="text" placeholder="1403-01-15" value="${escHtml(date)}" style="width:140px"
        oninput="loadAppointments(this.value)">
      <button class="btn btn-outline btn-sm" onclick="loadAppointments('')">نوبت‌های امروز</button>
    </div>
    ${list.length === 0 ? renderEmpty('هیچ نوبتی یافت نشد') : `
    <div class="card table-wrap">
      <table>
        <thead><tr>
          <th>#</th><th>بیمار</th><th>دندانپزشک</th><th>تاریخ</th><th>ساعت</th><th>نوع ویزیت</th><th>وضعیت</th><th>عملیات</th>
        </tr></thead>
        <tbody>
          ${list.map((a, i) => `<tr>
            <td>${i+1}</td>
            <td>${a.patient_id}</td>
            <td>${a.dentist_id}</td>
            <td>${escHtml(a.appointment_date)}</td>
            <td dir="ltr">${escHtml(a.appointment_time||'—')}</td>
            <td>${escHtml(a.visit_type||'—')}</td>
            <td>${statusBadge(a.status)}</td>
            <td style="white-space:nowrap">
              <button class="btn btn-outline btn-sm" onclick="changeApptStatus(${a.id},'${escHtml(a.status)}')">وضعیت</button>
              <button class="btn btn-danger btn-sm" onclick="deleteAppt(${a.id})">حذف</button>
            </td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>`}`;
}

function openApptForm() {
  const dentistOpts = _apptDentists.map(d =>
    `<option value="${d.id}">${escHtml(d.full_name)}</option>`).join('');
  const html = `
    <div class="modal-header"><h2>نوبت جدید</h2><button class="btn" onclick="closeModal()">✕</button></div>
    <form id="appt-form" onsubmit="saveAppt(event)">
      <div class="form-group"><label>شناسه بیمار *</label><input name="patient_id" type="number" required></div>
      <div class="form-group"><label>دندانپزشک *</label>
        <select name="dentist_id" required><option value="">انتخاب کنید</option>${dentistOpts}</select></div>
      <div class="form-row">
        <div class="form-group"><label>تاریخ نوبت (شمسی) *</label><input name="appointment_date" required placeholder="1403-01-15"></div>
        <div class="form-group"><label>ساعت</label><input name="appointment_time" placeholder="09:00" dir="ltr"></div>
      </div>
      <div class="form-group"><label>نوع ویزیت</label>
        <select name="visit_type">
          <option value="اولین ویزیت">اولین ویزیت</option>
          <option value="پیگیری">پیگیری</option>
          <option value="اورژانس">اورژانس</option>
          <option value="کنترل">کنترل</option>
        </select></div>
      <div class="form-group"><label>شکایت اصلی</label><textarea name="chief_complaint" rows="2"></textarea></div>
      <div class="modal-footer">
        <button type="submit" class="btn btn-primary">ذخیره</button>
        <button type="button" class="btn btn-outline" onclick="closeModal()">لغو</button>
      </div>
    </form>`;
  openModal(html);
}

async function saveAppt(e) {
  e.preventDefault();
  const data = getFormData(e.target);
  data.patient_id = parseInt(data.patient_id);
  data.dentist_id = parseInt(data.dentist_id);
  try {
    await api.post('/api/appointments', data);
    closeModal();
    toast('نوبت ثبت شد');
    await loadAppointments();
  } catch(err) { toast(err.message, 'error'); }
}

function changeApptStatus(id, current) {
  const statuses = ['نوبت‌دار', 'تکمیل شده', 'لغو شده', 'غایب'];
  const opts = statuses.map(s => `<option value="${s}" ${s===current?'selected':''}>${s}</option>`).join('');
  const html = `
    <div class="modal-header"><h2>تغییر وضعیت</h2><button class="btn" onclick="closeModal()">✕</button></div>
    <div class="form-group" style="margin:1rem 0"><label>وضعیت جدید</label>
      <select id="new-status">${opts}</select></div>
    <div class="modal-footer">
      <button class="btn btn-primary" onclick="applyStatus(${id})">ذخیره</button>
      <button class="btn btn-outline" onclick="closeModal()">لغو</button>
    </div>`;
  openModal(html);
}

async function applyStatus(id) {
  const status = document.getElementById('new-status').value;
  try {
    await api.patch(`/api/appointments/${id}/status`, { status });
    closeModal();
    toast('وضعیت بروزرسانی شد');
    await loadAppointments();
  } catch(err) { toast(err.message, 'error'); }
}

async function deleteAppt(id) {
  const ok = await confirmDialog('آیا می‌خواهید این نوبت را حذف کنید؟');
  if (!ok) return;
  try {
    await api.delete(`/api/appointments/${id}`);
    toast('نوبت حذف شد');
    await loadAppointments();
  } catch(err) { toast(err.message, 'error'); }
}
