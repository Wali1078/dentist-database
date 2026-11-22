async function initReports() {
  const el = document.getElementById('page-reports');
  el.innerHTML = `
    <div class="section-header"><h2>گزارشات</h2></div>
    <div style="display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:1.5rem">
      <div class="card" style="flex:1;min-width:220px">
        <h3 style="margin-bottom:.75rem">گزارش ماهانه</h3>
        <div class="form-row">
          <div class="form-group"><label>سال</label><input id="rep-year" type="number" value="1403" style="width:100%"></div>
          <div class="form-group"><label>ماه</label><input id="rep-month" type="number" min="1" max="12" value="1" style="width:100%"></div>
        </div>
        <button class="btn btn-primary btn-sm" onclick="loadMonthlyReport()">نمایش</button>
      </div>
      <div class="card" style="flex:1;min-width:220px">
        <h3 style="margin-bottom:.75rem">خلاصه مصارف</h3>
        <button class="btn btn-outline btn-sm" onclick="loadExpensesSummary()">بارگذاری</button>
      </div>
    </div>
    <div id="report-result"></div>`;
}

async function loadMonthlyReport() {
  const year  = parseInt(document.getElementById('rep-year').value);
  const month = parseInt(document.getElementById('rep-month').value);
  const el = document.getElementById('report-result');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const d = await api.get(`/api/reports/monthly?year=${year}&month=${month}`);
    el.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card"><span class="stat-value" style="color:var(--success)">${fmtMoney(d.revenue)}</span><span class="stat-label">درآمد</span></div>
        <div class="stat-card"><span class="stat-value" style="color:var(--danger)">${fmtMoney(d.expenses)}</span><span class="stat-label">مصارف</span></div>
        <div class="stat-card"><span class="stat-value" style="color:${d.profit>=0?'var(--success)':'var(--danger)'}">${fmtMoney(d.profit)}</span><span class="stat-label">سود خالص</span></div>
        <div class="stat-card"><span class="stat-value">${d.appointments}</span><span class="stat-label">نوبت‌ها</span></div>
        <div class="stat-card"><span class="stat-value">${d.new_patients}</span><span class="stat-label">بیماران جدید</span></div>
      </div>`;
  } catch(e) {
    el.innerHTML = `<p class="text-danger">${escHtml(e.message)}</p>`;
  }
}

async function loadExpensesSummary() {
  const el = document.getElementById('report-result');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const d = await api.get('/api/reports/expenses-summary');
    const rows = Object.entries(d.by_category).map(([cat, total]) =>
      `<tr><td>${escHtml(cat)}</td><td>${fmtMoney(total)}</td></tr>`).join('');
    el.innerHTML = `
      <div class="card table-wrap">
        <table>
          <thead><tr><th>کتگوری</th><th>مجموع</th></tr></thead>
          <tbody>${rows || '<tr><td colspan="2" class="text-muted">داده‌ای وجود ندارد</td></tr>'}</tbody>
          <tfoot><tr><th>مجموع کل</th><th>${fmtMoney(d.total)}</th></tr></tfoot>
        </table>
      </div>`;
  } catch(e) {
    el.innerHTML = `<p class="text-danger">${escHtml(e.message)}</p>`;
  }
}
