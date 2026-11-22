/* ── Page registry ───────────────────────────────────────────────────────── */
const PAGES = {
  dashboard:    { title: 'داشبورد',      init: initDashboard },
  patients:     { title: 'بیماران',      init: initPatients },
  appointments: { title: 'نوبت‌ها',      init: initAppointments },
  dental:       { title: 'سابقه دندان', init: initDental },
  billing:      { title: 'صورت‌حساب',   init: initBilling },
  inventory:    { title: 'انبار',        init: initInventory },
  staff:        { title: 'کارمندان',     init: initStaff },
  expenses:     { title: 'مصارف',        init: initExpenses },
  reports:      { title: 'گزارشات',      init: initReports },
};

let _currentPage = null;

async function navigate(page) {
  if (!PAGES[page]) return;

  // Hide all pages
  Object.keys(PAGES).forEach(p => {
    const el = document.getElementById(`page-${p}`);
    if (el) el.classList.add('hidden');
  });

  // Show target
  const el = document.getElementById(`page-${page}`);
  if (el) el.classList.remove('hidden');

  // Update nav active state
  document.querySelectorAll('.nav-link').forEach(a => {
    a.classList.toggle('active', a.dataset.page === page);
  });

  // Update title
  document.getElementById('page-title').textContent = PAGES[page].title;

  _currentPage = page;

  // Init page
  await PAGES[page].init();
}

// Wire nav links
document.querySelectorAll('.nav-link[data-page]').forEach(a => {
  a.addEventListener('click', () => {
    navigate(a.dataset.page);
    // On mobile close sidebar
    if (window.innerWidth <= 768) {
      document.getElementById('sidebar').classList.remove('open');
    }
  });
});

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// Bootstrap
navigate('dashboard');
