"""
Full Playwright CRUD browser tests for Darya at 1366x768 and 1920x1080.
"""
import requests
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765"
CHROME = "/usr/bin/google-chrome"
RESOLUTIONS = [(1366, 768), (1920, 1080)]


def api(method, path, **kwargs):
    r = requests.request(method, URL + path, **kwargs)
    r.raise_for_status()
    return r.json()


def open_page(page, name):
    page.click(f'[data-page="{name}"]')
    page.wait_for_selector(f"#page-{name}:not(.hidden)", timeout=5000)


def close_modal(page):
    page.locator('.modal-header .btn').first.click()
    page.wait_for_selector(".modal", state="hidden", timeout=3000)


def run_all_checks(page, width, height):
    checks = []
    TODAY = api("GET", "/api/reports/dashboard")["today"]  # e.g. "1405-09-01"

    def check(name, fn):
        try:
            fn()
            checks.append(("pass", name))
        except Exception as e:
            checks.append(("fail", name, str(e)[:160]))
            raise

    # ── Clean up any data from previous runs ──────────────────────────────────
    # (live server keeps DB between tests; seed fresh data each run)

    # ── STAFF: Create ─────────────────────────────────────────────────────────
    def test_staff_create():
        open_page(page, "staff")
        page.click('button[onclick="openStaffForm()"]')
        page.wait_for_selector(".modal", timeout=4000)
        page.locator('[name="full_name"]').fill("دکتر آزمایشی")
        page.locator('[name="role"]').select_option("دندانپزشک")
        page.locator('[name="phone"]').fill("0700999001")
        page.locator('#staff-form button[type="submit"]').click()
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        page.wait_for_selector('#page-staff td:has-text("دکتر آزمایشی")', timeout=5000)
    check("staff: create", test_staff_create)

    all_staff = api("GET", "/api/staff")
    dentist = next((s for s in all_staff if "آزمایشی" in s["full_name"]), None)
    assert dentist, "Dentist not found via API"
    dentist_id = dentist["id"]

    # ── STAFF: Edit ───────────────────────────────────────────────────────────
    def test_staff_edit():
        open_page(page, "staff")
        page.locator(f'button[onclick="openStaffForm({dentist_id})"]').click()
        page.wait_for_selector(".modal", timeout=4000)
        page.locator('[name="full_name"]').fill("دکتر آزمایشی ویرایش")
        page.locator(f'#staff-form button[type="submit"]').click()
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        page.wait_for_selector('#page-staff td:has-text("دکتر آزمایشی ویرایش")', timeout=5000)
    check("staff: edit", test_staff_edit)

    # ── PATIENTS: Create ──────────────────────────────────────────────────────
    def test_patient_create():
        open_page(page, "patients")
        page.click('button[onclick="openPatientForm()"]')
        page.wait_for_selector(".modal", timeout=4000)
        page.locator('[name="full_name"]').fill("بیمار آزمایشی")
        page.locator('[name="phone"]').fill("0700111222")
        page.locator('[name="gender"]').select_option("زن")
        page.locator('[name="province"]').fill("کابل")
        page.locator('#patient-form button[type="submit"]').click()
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        page.wait_for_selector('#page-patients td:has-text("بیمار آزمایشی")', timeout=5000)
    check("patients: create", test_patient_create)

    all_patients = api("GET", "/api/patients")
    patient = next((p for p in all_patients if "بیمار آزمایشی" == p["full_name"]), None)
    assert patient, "Patient not found via API"
    patient_id = patient["id"]

    # ── PATIENTS: Search ──────────────────────────────────────────────────────
    def test_patient_search():
        open_page(page, "patients")
        page.locator("#patient-search").fill("آزمایشی")
        page.wait_for_timeout(700)
        rows = page.locator('#page-patients tbody tr').count()
        assert rows >= 1, f"Search returned {rows} rows"
    check("patients: search", test_patient_search)

    # ── PATIENTS: Edit ────────────────────────────────────────────────────────
    def test_patient_edit():
        open_page(page, "patients")
        page.locator("#patient-search").fill("")
        page.wait_for_timeout(700)
        page.locator(f'button[onclick="openPatientForm({patient_id})"]').click()
        page.wait_for_selector(".modal", timeout=4000)
        name_field = page.locator('[name="full_name"]')
        name_field.fill("بیمار ویرایش‌شده")
        page.locator('#patient-form button[type="submit"]').click()
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        page.wait_for_selector('#page-patients td:has-text("بیمار ویرایش‌شده")', timeout=5000)
    check("patients: edit", test_patient_edit)

    # ── APPOINTMENTS: Create ──────────────────────────────────────────────────
    def test_appointment_create():
        open_page(page, "appointments")
        page.click('button[onclick="openApptForm()"]')
        page.wait_for_selector(".modal", timeout=4000)
        page.locator('[name="patient_id"]').fill(str(patient_id))
        page.locator('[name="dentist_id"]').select_option(str(dentist_id))
        page.locator('[name="appointment_date"]').fill(TODAY)  # today → shows in default view
        page.locator('[name="appointment_time"]').fill("10:00")
        page.locator('#appt-form button[type="submit"]').click()
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        # After save, loadAppointments() reloads today's list — patient_id appears
        page.wait_for_selector(f'#page-appointments td:has-text("{patient_id}")', timeout=5000)
    check("appointments: create", test_appointment_create)

    appts = api("GET", "/api/appointments")
    appt = next((a for a in appts if a["patient_id"] == patient_id), None)
    assert appt, "Appointment not found via API"
    appt_id = appt["id"]

    # ── APPOINTMENTS: Status change ───────────────────────────────────────────
    def test_appointment_status():
        open_page(page, "appointments")
        # Click the وضعیت button for the specific appointment row
        page.locator(f'button[onclick*="changeApptStatus({appt_id},"]').click()
        page.wait_for_selector(".modal", timeout=4000)
        page.locator("#new-status").select_option("تکمیل شده")
        # Save button is unique in modal — use text
        page.locator('.modal button:has-text("ذخیره")').click()
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        page.wait_for_selector('#page-appointments .badge:has-text("تکمیل شده")', timeout=5000)
    check("appointments: change status", test_appointment_status)

    # ── APPOINTMENTS: Delete ──────────────────────────────────────────────────
    def test_appointment_delete():
        # Create a fresh appointment to delete (use today so it shows in default view)
        extra = api("POST", "/api/appointments", json={
            "patient_id": patient_id,
            "dentist_id": dentist_id,
            "appointment_date": TODAY,
        })
        extra_id = extra["id"]
        open_page(page, "appointments")
        page.locator(f'button[onclick="deleteAppt({extra_id})"]').click()
        page.wait_for_selector('#conf-yes', timeout=4000)
        page.locator('#conf-yes').click()
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        page.wait_for_timeout(500)
        # Verify deleted via API
        import requests as _r
        r = _r.get(f"{URL}/api/appointments/{extra_id}")
        assert r.status_code == 404
    check("appointments: delete", test_appointment_delete)

    # ── INVENTORY: Create ─────────────────────────────────────────────────────
    def test_inventory_create():
        open_page(page, "inventory")
        page.click('button[onclick="openItemForm()"]')
        page.wait_for_selector(".modal", timeout=4000)
        page.locator('[name="item_name"]').fill("کامپوزیت آزمایشی")
        page.locator('[name="quantity_in_stock"]').fill("20")
        page.locator('[name="reorder_level"]').fill("5")
        page.locator('[name="cost_per_unit"]').fill("200")
        page.locator('#item-form button[type="submit"]').click()
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        page.wait_for_selector('#page-inventory td:has-text("کامپوزیت آزمایشی")', timeout=5000)
    check("inventory: create", test_inventory_create)

    inv_list = api("GET", "/api/inventory")
    inv_item = next((i for i in inv_list if "کامپوزیت آزمایشی" == i["item_name"]), None)
    assert inv_item, "Inventory item not found"
    inv_item_id = inv_item["id"]

    # ── INVENTORY: Edit ───────────────────────────────────────────────────────
    def test_inventory_edit():
        open_page(page, "inventory")
        page.locator(f'button[onclick="openItemForm({inv_item_id})"]').click()
        page.wait_for_selector(".modal", timeout=4000)
        page.locator('[name="cost_per_unit"]').fill("250")
        page.locator(f'#item-form button[type="submit"]').click()
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        updated = api("GET", f"/api/inventory/{inv_item_id}")
        assert float(updated["cost_per_unit"]) == 250
    check("inventory: edit", test_inventory_edit)

    # ── INVENTORY: Low-stock filter ───────────────────────────────────────────
    def test_inventory_low_stock():
        # Create a low-stock item
        api("POST", "/api/inventory", json={
            "item_name": "ماده کم‌موجود",
            "quantity_in_stock": 1,
            "reorder_level": 10,
            "cost_per_unit": 50,
        })
        open_page(page, "dashboard")
        open_page(page, "inventory")
        # In all-items view, normal item IS visible
        page.wait_for_selector('#page-inventory td:has-text("کامپوزیت آزمایشی")', timeout=5000)
        # Click کم‌موجود filter — wait for normal item to DISAPPEAR (confirms filter applied)
        with page.expect_response(lambda r: "/api/inventory/low-stock" in r.url):
            page.locator('button[onclick="loadInventory(true)"]').click()
        page.wait_for_selector('#page-inventory td:has-text("کامپوزیت آزمایشی")',
                                state="hidden", timeout=5000)
        # Low-stock item should now appear
        page.wait_for_selector('#page-inventory td:has-text("ماده کم‌موجود")', timeout=3000)
    check("inventory: low-stock filter", test_inventory_low_stock)

    # ── INVENTORY: Delete ─────────────────────────────────────────────────────
    def test_inventory_delete():
        extra = api("POST", "/api/inventory", json={
            "item_name": "ماده حذفی",
            "quantity_in_stock": 5,
            "reorder_level": 2,
            "cost_per_unit": 10,
        })
        extra_id = extra["id"]
        open_page(page, "inventory")
        page.locator('button[onclick="loadInventory(false)"]').click()
        page.wait_for_selector('#page-inventory td:has-text("ماده حذفی")', timeout=5000)
        page.locator(f'button[onclick="deleteItem({extra_id})"]').click()
        page.wait_for_selector('#conf-yes', timeout=4000)
        page.locator('#conf-yes').click()
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        page.wait_for_timeout(500)
        import requests as _r
        assert _r.get(f"{URL}/api/inventory/{extra_id}").status_code == 404
    check("inventory: delete", test_inventory_delete)

    # ── EXPENSES: Create ──────────────────────────────────────────────────────
    def test_expense_create():
        open_page(page, "expenses")
        page.click('button[onclick="openExpenseForm()"]')
        page.wait_for_selector(".modal", timeout=4000)
        page.locator('[name="category"]').select_option("برق")
        page.locator('[name="amount"]').fill("3500")
        page.locator('[name="expense_date"]').fill("1403-06-15")
        page.locator('#exp-form button[type="submit"]').click()
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        page.wait_for_selector('#page-expenses td:has-text("برق")', timeout=5000)
    check("expenses: create", test_expense_create)

    exp_list = api("GET", "/api/expenses")
    expense = next((e for e in exp_list if e["category"] == "برق"), None)
    assert expense, "Expense not found"
    expense_id = expense["id"]

    # ── EXPENSES: Category filter ─────────────────────────────────────────────
    def test_expense_filter():
        api("POST", "/api/expenses", json={"category": "معاش", "amount": 15000, "expense_date": "1403-06-01"})
        open_page(page, "dashboard")
        open_page(page, "expenses")
        page.locator('#page-expenses select').select_option("برق")
        page.wait_for_timeout(600)
        maash = page.locator('#page-expenses td:has-text("معاش")').count()
        assert maash == 0, "معاش row visible when filtering for برق"
    check("expenses: category filter", test_expense_filter)

    # ── EXPENSES: Delete ──────────────────────────────────────────────────────
    def test_expense_delete():
        open_page(page, "expenses")
        page.locator('#page-expenses select').select_option("")  # all
        page.wait_for_timeout(600)
        page.locator(f'button[onclick="deleteExpense({expense_id})"]').click()
        page.wait_for_selector('#conf-yes', timeout=4000)
        page.locator('#conf-yes').click()
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        page.wait_for_timeout(500)
        import requests as _r
        assert _r.get(f"{URL}/api/expenses/{expense_id}").status_code == 404
    check("expenses: delete", test_expense_delete)

    # ── BILLING: Create invoice ───────────────────────────────────────────────
    def test_billing_create():
        open_page(page, "billing")
        page.click('button[onclick="openInvoiceForm()"]')
        page.wait_for_selector(".modal", timeout=4000)
        page.locator('[name="patient_id"]').fill(str(patient_id))
        page.locator('[name="total_amount"]').fill("5000")
        page.locator('[name="discount_amount"]').fill("500")
        page.locator('#inv-form button[type="submit"]').click()
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        page.wait_for_selector(f'#page-billing td:has-text("{patient_id}")', timeout=5000)
        page.wait_for_selector('#page-billing .badge:has-text("پرداخت نشده")', timeout=3000)
    check("billing: create invoice", test_billing_create)

    invoices = api("GET", "/api/billing")
    invoice = next((i for i in invoices if i["patient_id"] == patient_id), None)
    assert invoice, "Invoice not found"
    invoice_id = invoice["id"]

    # ── BILLING: Partial payment → قسمی ──────────────────────────────────────
    def test_billing_partial_payment():
        open_page(page, "billing")
        # Payment button: onclick="openPaymentForm(ID, BALANCE)"
        page.locator(f'#page-billing button[onclick*="openPaymentForm({invoice_id},"]').click()
        page.wait_for_selector(".modal", timeout=4000)
        page.locator('[name="amount"]').fill("2000")
        page.locator('#pay-form button[type="submit"]').click()
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        page.wait_for_selector('#page-billing .badge:has-text("قسمی")', timeout=5000)
    check("billing: partial payment → قسمی", test_billing_partial_payment)

    # ── BILLING: Full payment → پرداخت شده ───────────────────────────────────
    def test_billing_full_payment():
        open_page(page, "billing")
        updated = api("GET", f"/api/billing/{invoice_id}")
        remaining = float(updated["balance_due"])
        # Use invoice_id in onclick — balance changed so use * contains-selector
        page.locator(f'#page-billing button[onclick*="openPaymentForm({invoice_id},"]').click()
        page.wait_for_selector(".modal", timeout=4000)
        page.locator('[name="amount"]').fill(str(int(remaining)))
        page.locator('#pay-form button[type="submit"]').click()
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        page.wait_for_selector('#page-billing .badge:has-text("پرداخت شده")', timeout=5000)
    check("billing: full payment → پرداخت شده", test_billing_full_payment)

    # ── DENTAL: Load chart ────────────────────────────────────────────────────
    def test_dental_chart_load():
        open_page(page, "dental")
        page.locator("#chart-pid").fill(str(patient_id))
        page.click('button[onclick="loadChart()"]')
        page.wait_for_selector("#chart-container .tooth-grid", timeout=8000)
        teeth = page.locator("#chart-container .tooth-btn").count()
        assert teeth >= 32, f"Expected >=32 tooth-btn elements, got {teeth}"
    check("dental: load chart", test_dental_chart_load)

    # ── DENTAL: Add record ────────────────────────────────────────────────────
    def test_dental_add_record():
        open_page(page, "dental")
        page.locator("#chart-pid").fill(str(patient_id))
        page.click('button[onclick="loadChart()"]')
        page.wait_for_selector("#chart-container .tooth-grid", timeout=8000)
        page.click('button[onclick="openAddRecord()"]')
        page.wait_for_selector(".modal", timeout=4000)
        page.locator('[name="tooth_number"]').fill("11")
        page.locator('[name="dentist_id"]').fill(str(dentist_id))
        page.locator('[name="condition"]').fill("پوسیدگی")
        page.locator('[name="treatment_performed"]').fill("پر کردن")
        page.locator('#dental-form button[type="submit"]').click()
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        # Verify via API
        chart = api("GET", f"/api/dental/chart/{patient_id}")
        t11 = next((t for t in chart if t["tooth_number"] == 11), None)
        assert t11, "Tooth 11 not in chart after adding record"
    check("dental: add record", test_dental_add_record)

    # ── DENTAL: Tooth click opens detail ──────────────────────────────────────
    def test_dental_tooth_click():
        open_page(page, "dental")
        page.locator("#chart-pid").fill(str(patient_id))
        page.click('button[onclick="loadChart()"]')
        page.wait_for_selector("#chart-container .tooth-grid", timeout=8000)
        # Click tooth 11 button (onclick="openToothDetail(11)")
        page.locator('button[onclick="openToothDetail(11)"]').click()
        page.wait_for_selector(".modal", timeout=4000)
        modal_text = page.locator(".modal").text_content()
        assert "11" in modal_text, "Modal doesn't mention tooth 11"
        close_modal(page)
    check("dental: tooth click shows detail", test_dental_tooth_click)

    # ── REPORTS: Monthly ──────────────────────────────────────────────────────
    def test_reports_monthly():
        open_page(page, "reports")
        page.locator("#rep-year").fill("1403")
        page.locator("#rep-month").fill("6")
        page.locator('#page-reports button[onclick="loadMonthlyReport()"]').click()
        page.wait_for_selector("#report-result .stat-card", timeout=8000)
        cards = page.locator("#report-result .stat-card").count()
        assert cards >= 4, f"Expected >=4 stat cards, got {cards}"
    check("reports: monthly", test_reports_monthly)

    # ── REPORTS: Expenses summary ─────────────────────────────────────────────
    def test_reports_expenses_summary():
        open_page(page, "reports")
        page.locator('#page-reports button[onclick="loadExpensesSummary()"]').click()
        page.wait_for_selector("#report-result table", timeout=8000)
        rows = page.locator("#report-result tbody tr").count()
        assert rows >= 1, "Expenses summary has no rows"
    check("reports: expenses summary", test_reports_expenses_summary)

    # ── PATIENTS: Delete (no history) ─────────────────────────────────────────
    def test_patient_delete():
        fresh = api("POST", "/api/patients", json={"full_name": "بیمار حذفی"})
        fresh_id = fresh["id"]
        open_page(page, "patients")
        page.locator("#patient-search").fill("بیمار حذفی")
        page.wait_for_timeout(700)
        page.locator(f'button[onclick="deletePatient({fresh_id})"]').click()
        page.wait_for_selector('#conf-yes', timeout=4000)
        page.locator('#conf-yes').click()
        page.wait_for_selector(".modal", state="hidden", timeout=5000)
        page.wait_for_timeout(500)
        import requests as _r
        assert _r.get(f"{URL}/api/patients/{fresh_id}").status_code == 404
    check("patients: delete (no history)", test_patient_delete)

    return checks


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    all_passed = True

    with sync_playwright() as p:
        for width, height in RESOLUTIONS:
            print(f"\n{'='*58}")
            print(f"  {width}×{height}")
            print(f"{'='*58}")

            browser = p.chromium.launch(
                executable_path=CHROME,
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda e: print(f"  [pageerror] {e}"))

            page.goto(URL, wait_until="networkidle", timeout=15000)
            page.wait_for_selector(".stat-card", timeout=8000)

            try:
                checks = run_all_checks(page, width, height)
            except AssertionError as e:
                print(f"  ABORTED: {e}")
                all_passed = False
                browser.close()
                continue

            fails = []
            for c in checks:
                if c[0] == "pass":
                    print(f"  ✓ {c[1]}")
                else:
                    print(f"  ✗ {c[1]}: {c[2]}")
                    fails.append(c[1])

            if fails:
                all_passed = False
                print(f"\n  {len(fails)}/{len(checks)} FAILED")
            else:
                print(f"\n  All {len(checks)} checks PASSED at {width}×{height}")

            browser.close()

    print(f"\n{'='*58}")
    print("  ALL BROWSER CRUD TESTS PASSED" if all_passed else "  SOME TESTS FAILED — see above")
    print(f"{'='*58}\n")

    if not all_passed:
        raise SystemExit(1)


run()
