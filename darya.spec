# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('frontend', 'frontend'),
        ('backend',  'backend'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn._types',
        'fastapi',
        'sqlalchemy.dialects.sqlite',
        'jdatetime',
        'pydantic',
        'email.mime.text',
        'email.mime.multipart',
        'backend.models.patient',
        'backend.models.staff',
        'backend.models.appointment',
        'backend.models.dental_chart',
        'backend.models.invoice',
        'backend.models.inventory',
        'backend.models.expense',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Darya',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=None,
)
