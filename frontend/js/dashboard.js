async function initDashboard() {
  const el = document.getElementById('page-dashboard');
  el.innerHTML = '<div class="loading-overlay" style="position:static;padding:3rem;text-align:center"><div class="spinner"></div></div>';
  try {
    const d = await api.get('/api/reports/dashboard');
    el.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card">
          <span class="stat-value">${d.today_appointments}</span>
          <span class="stat-label">نوبت‌های امروز</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">${d.total_patients}</span>
          <span class="stat-label">تعداد بیماران</span>
        </div>
        <div class="stat-card">
          <span class="stat-value" style="color:var(--success)">${fmtMoney(d.month_revenue)}</span>
          <span class="stat-label">درآمد این ماه</span>
        </div>
        <div class="stat-card">
          <span class="stat-value" style="color:var(--danger)">${fmtMoney(d.month_expenses)}</span>
          <span class="stat-label">مصارف این ماه</span>
        </div>
        <div class="stat-card">
          <span class="stat-value" style="color:${d.month_profit >= 0 ? 'var(--success)' : 'var(--danger)'}">
            ${fmtMoney(d.month_profit)}
          </span>
          <span class="stat-label">سود خالص</span>
        </div>
        <div class="stat-card">
          <span class="stat-value" style="color:var(--warning)">${d.unpaid_invoices}</span>
          <span class="stat-label">صورت‌حساب پرداخت نشده</span>
        </div>
      </div>
      <div class="card" style="margin-top:1rem">
        <p class="text-muted" style="font-size:.88rem">تاریخ امروز: <strong>${d.today}</strong></p>
      </div>`;
  } catch(e) {
    el.innerHTML = `<div class="card"><p class="text-danger">خطا در بارگذاری: ${escHtml(e.message)}</p></div>`;
  }
}
