/* ── Dental chart – FDI notation ─────────────────────────────────────────── */
const ADULT_UPPER = [18,17,16,15,14,13,12,11, 21,22,23,24,25,26,27,28];
const ADULT_LOWER = [48,47,46,45,44,43,42,41, 31,32,33,34,35,36,37,38];
const CHILD_UPPER = [55,54,53,52,51, 61,62,63,64,65];
const CHILD_LOWER = [85,84,83,82,81, 71,72,73,74,75];

let _chartPatientId = null;
let _chartData = {};

async function initDental() {
  const el = document.getElementById('page-dental');
  el.innerHTML = `
    <div class="section-header"><h2>سابقه دندان</h2></div>
    <div class="card" style="margin-bottom:1rem;display:flex;gap:1rem;align-items:center">
      <input type="number" id="chart-pid" placeholder="شناسه بیمار" style="width:160px">
      <button class="btn btn-primary btn-sm" onclick="loadChart()">نمایش نمودار</button>
    </div>
    <div id="chart-container"></div>`;
}

async function loadChart() {
  const pid = parseInt(document.getElementById('chart-pid').value);
  if (!pid) { toast('شناسه بیمار را وارد کنید', 'error'); return; }
  _chartPatientId = pid;
  const c = document.getElementById('chart-container');
  c.innerHTML = '<div class="spinner"></div>';
  try {
    const records = await api.get(`/api/dental/chart/${pid}`);
    _chartData = {};
    records.forEach(r => { _chartData[r.tooth_number] = r; });
    renderChart(c);
  } catch(e) { c.innerHTML = `<p class="text-danger">${escHtml(e.message)}</p>`; }
}

function toothColor(tn) {
  const r = _chartData[tn];
  if (!r || !r.latest) return '';
  const s = r.latest.treatment_status;
  if (s === 'تکمیل شده') return 'treated';
  if (s === 'پلان شده')  return 'planned';
  if (s === 'کشیده شده') return 'missing';
  return 'healthy';
}

function renderToothRow(teeth) {
  return teeth.map(tn => `
    <button class="tooth-btn ${toothColor(tn)}" title="دندان ${tn}" onclick="openToothDetail(${tn})">
      <span>${tn}</span>
      ${_chartData[tn] ? '<span class="dot" style="color:var(--primary)"></span>' : ''}
    </button>`).join('');
}

function renderChart(c) {
  c.innerHTML = `
    <div class="card">
      <h3 style="margin-bottom:.75rem">فک بالا – دائمی</h3>
      <div class="tooth-grid">${renderToothRow(ADULT_UPPER)}</div>
      <div class="jaw-label">──────────────── خط وسط ────────────────</div>
      <div class="tooth-grid">${renderToothRow(ADULT_LOWER)}</div>
      <h3 style="margin:1.25rem 0 .75rem">شیری – بالا</h3>
      <div class="tooth-grid" style="grid-template-columns:repeat(10,1fr)">${renderToothRow(CHILD_UPPER)}</div>
      <div class="tooth-grid" style="grid-template-columns:repeat(10,1fr)">${renderToothRow(CHILD_LOWER)}</div>
      <div style="margin-top:1.25rem">
        <button class="btn btn-primary btn-sm" onclick="openAddRecord()">+ افزودن سابقه</button>
      </div>
    </div>`;
}

function openToothDetail(tn) {
  const rec = _chartData[tn];
  if (!rec) {
    const html = `
      <div class="modal-header"><h2>دندان ${tn}</h2><button class="btn" onclick="closeModal()">✕</button></div>
      <p class="text-muted">هیچ سابقه‌ای برای این دندان ثبت نشده.</p>
      <div class="modal-footer">
        <button class="btn btn-primary" onclick="closeModal();openAddRecord(${tn})">+ افزودن</button>
        <button class="btn btn-outline" onclick="closeModal()">بستن</button>
      </div>`;
    openModal(html);
    return;
  }
  const rows = rec.history.map(h => `
    <tr>
      <td>${escHtml(h.treatment_date||'—')}</td>
      <td>${escHtml(h.condition||'—')}</td>
      <td>${escHtml(h.treatment_performed||'—')}</td>
      <td>${statusBadge(h.treatment_status||'')}</td>
    </tr>`).join('');
  const html = `
    <div class="modal-header"><h2>دندان ${tn} – سابقه</h2><button class="btn" onclick="closeModal()">✕</button></div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>تاریخ</th><th>وضعیت</th><th>درمان</th><th>مرحله</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    <div class="modal-footer">
      <button class="btn btn-primary btn-sm" onclick="closeModal();openAddRecord(${tn})">+ افزودن</button>
      <button class="btn btn-outline" onclick="closeModal()">بستن</button>
    </div>`;
  openModal(html);
}

function openAddRecord(presetTooth = null) {
  const html = `
    <div class="modal-header"><h2>افزودن سابقه دندانی</h2><button class="btn" onclick="closeModal()">✕</button></div>
    <form id="dental-form" onsubmit="saveDentalRecord(event)">
      <div class="form-row">
        <div class="form-group"><label>شماره دندان *</label>
          <input name="tooth_number" type="number" required value="${presetTooth||''}"></div>
        <div class="form-group"><label>دندانپزشک *</label>
          <input name="dentist_id" type="number" required></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>وضعیت دندان</label><input name="condition"></div>
        <div class="form-group"><label>درمان انجام شده</label><input name="treatment_performed"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>مرحله درمان</label>
          <select name="treatment_status">
            <option value="پلان شده">پلان شده</option>
            <option value="در حال انجام">در حال انجام</option>
            <option value="تکمیل شده">تکمیل شده</option>
            <option value="کشیده شده">کشیده شده</option>
          </select></div>
        <div class="form-group"><label>تاریخ درمان (شمسی)</label>
          <input name="treatment_date" placeholder="1403-01-15"></div>
      </div>
      <div class="form-group"><label>یادداشت</label><textarea name="notes" rows="2"></textarea></div>
      <div class="modal-footer">
        <button type="submit" class="btn btn-primary">ذخیره</button>
        <button type="button" class="btn btn-outline" onclick="closeModal()">لغو</button>
      </div>
    </form>`;
  openModal(html);
}

async function saveDentalRecord(e) {
  e.preventDefault();
  const data = getFormData(e.target);
  data.patient_id = _chartPatientId;
  data.tooth_number = parseInt(data.tooth_number);
  data.dentist_id   = parseInt(data.dentist_id);
  try {
    await api.post('/api/dental/records', data);
    closeModal();
    toast('سابقه ثبت شد');
    await loadChart();
  } catch(err) { toast(err.message, 'error'); }
}
