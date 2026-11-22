from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from backend.database import init_db
from backend.routes import (
    patients, staff, appointments, dental_chart,
    billing, inventory, expenses, reports, settings,
)

app = FastAPI(title="دریا - سیستم مدیریت کلینیک دندانپزشکی", version="1.0.0")

# Initialize DB on startup
@app.on_event("startup")
def on_startup():
    init_db()

# API routers
app.include_router(patients.router)
app.include_router(staff.router)
app.include_router(appointments.router)
app.include_router(dental_chart.router)
app.include_router(billing.router)
app.include_router(inventory.router)
app.include_router(expenses.router)
app.include_router(reports.router)
app.include_router(settings.router)

# Serve frontend static files
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/", include_in_schema=False)
    def serve_index():
        return FileResponse(str(frontend_dir / "index.html"))

    @app.get("/{path:path}", include_in_schema=False)
    def serve_spa(path: str):
        file_path = frontend_dir / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dir / "index.html"))
