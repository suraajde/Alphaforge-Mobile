# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

added_files = [
    ('VERSION.md', '.'),
]

if os.path.exists('resources'):
    added_files.append(('resources', 'resources'))

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'pandas',
        'yfinance',
        'yaml',
        'config.path_config',
        'core.version',
        'app.main_window',
        'app.screens.dashboard',
        'app.screens.stock_explorer',
        'app.screens.research_radar',
        'app.screens.portfolio',
        'app.screens.portfolio_health',
        'app.screens.portfolio_action_center',
        'app.screens.watchtower',
        'app.screens.settings',
        'services.portfolio_health_service',
        'services.alert_center_service',
        'services.alpha12_stability_service',
        'services.decision_audit_service',
        'services.drift_detection_service',
        'services.portfolio_intelligence_service',
        'services.portfolio_opportunity_service',
        'services.portfolio_risk_intelligence_service',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tests', 'pytest', '.pytest_tmp'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AlphaForge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AlphaForge-v1.0.0-Windows',
)
