from fastapi import APIRouter, HTTPException
from pathlib import Path
import shutil, datetime, os
from backend.database import _resolve_db_path

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/info")
def info():
    db_path = _resolve_db_path()
    return {
        "app": "دریا",
        "version": "1.0.0",
        "db_path": str(db_path),
        "db_exists": db_path.exists(),
        "db_size_kb": round(db_path.stat().st_size / 1024, 1) if db_path.exists() else 0,
    }


@router.post("/backup")
def backup():
    db_path = _resolve_db_path()
    if not db_path.exists():
        raise HTTPException(404, "دیتابیس پیدا نشد")
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"clinic_backup_{ts}.db"
    backup_path = db_path.parent / backup_name
    shutil.copy2(db_path, backup_path)
    return {"message": "بیکاپ ساخته شد", "backup_path": str(backup_path), "backup_name": backup_name}
