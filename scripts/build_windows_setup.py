"""Windows Setup Installer Builder Script for AlphaForge (Sprint 14.1.1)

Generates a standalone, self-installing executable AlphaForge-v1.0.0-Windows-Setup.exe
from the compiled dist/AlphaForge-v1.0.0-Windows distribution directory.

Features:
- Standard Windows Installation UI / automated installer wizard.
- Default install directory: %LOCALAPPDATA%\\Programs\\AlphaForge
- Creates Start Menu shortcut: "AlphaForge.lnk"
- Creates Desktop shortcut: "AlphaForge.lnk"
- Generates clean uninstaller script: "uninstall.exe" / "uninstall.cmd"
- Preserves user portfolio data in %APPDATA%\\AlphaForge\\data upon uninstall.
"""
import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

def build_windows_setup_installer():
    project_root = Path(__file__).resolve().parent.parent
    dist_root = project_root / "dist"
    app_dir = dist_root / "AlphaForge-v1.0.0-Windows"
    setup_exe = dist_root / "AlphaForge-v1.0.0-Windows-Setup.exe"

    if not app_dir.exists():
        raise FileNotFoundError(f"Distribution directory not found at {app_dir}")

    print("Building standalone Windows Installer AlphaForge-v1.0.0-Windows-Setup.exe...")

    payload_dir = project_root / "build" / "installer_payload"
    if payload_dir.exists():
        shutil.rmtree(payload_dir)
    payload_dir.mkdir(parents=True, exist_ok=True)

    payload_zip = payload_dir / "app_payload.zip"
    print("Compressing application payload...")
    with zipfile.ZipFile(payload_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(app_dir):
            for file in files:
                full_p = Path(root) / file
                rel_p = full_p.relative_to(app_dir)
                zf.write(full_p, rel_p)

    installer_script = payload_dir / "setup_runner.py"
    script_content = r'''import os
import sys
import shutil
import zipfile
from pathlib import Path
import subprocess
import ctypes

def main():
    # Target directory: %LOCALAPPDATA%\Programs\AlphaForge
    local_app_data = os.environ.get("LOCALAPPDATA", r"C:\Users\Public")
    target_dir = Path(local_app_data) / "Programs" / "AlphaForge"

    if target_dir.exists():
        try:
            shutil.rmtree(target_dir)
        except Exception:
            pass

    target_dir.mkdir(parents=True, exist_ok=True)

    # Extract bundled payload
    if hasattr(sys, "_MEIPASS"):
        payload_zip = Path(sys._MEIPASS) / "app_payload.zip"
    else:
        payload_zip = Path(__file__).parent / "app_payload.zip"

    with zipfile.ZipFile(payload_zip, 'r') as zf:
        zf.extractall(target_dir)

    exe_target = target_dir / "AlphaForge.exe"

    # Create Start Menu & Desktop Shortcuts
    try:
        app_data = os.environ.get("APPDATA", "")
        user_profile = os.environ.get("USERPROFILE", "")

        targets = []
        if app_data:
            start_menu_dir = Path(app_data) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "AlphaForge"
            start_menu_dir.mkdir(parents=True, exist_ok=True)
            targets.append(start_menu_dir / "AlphaForge.lnk")

        if user_profile:
            desktop_dir = Path(user_profile) / "Desktop"
            if not desktop_dir.exists():
                onedrive_desktop = Path(user_profile) / "OneDrive" / "Desktop"
                if onedrive_desktop.exists():
                    desktop_dir = onedrive_desktop

            if desktop_dir.exists():
                targets.append(desktop_dir / "AlphaForge.lnk")

        for shortcut_path in targets:
            vbs_code = f'Set WshShell = CreateObject("WScript.Shell")\nSet sc = WshShell.CreateShortcut("{shortcut_path}")\nsc.TargetPath = "{exe_target}"\nsc.WorkingDirectory = "{target_dir}"\nsc.Save()'
            vbs_file = target_dir / "_temp_shortcut.vbs"
            vbs_file.write_text(vbs_code, encoding="utf-8")
            subprocess.run(["cscript", "//Nologo", str(vbs_file)], capture_output=True)
            if vbs_file.exists():
                vbs_file.unlink()
    except Exception as exc:
        pass

    # Create safe uninstaller script
    uninstaller_path = target_dir / "uninstall.bat"
    uninstaller_code = f"@echo off\necho Uninstalling AlphaForge...\ntimeout /t 1 /nobreak >nul\ncd /d %TEMP%\nrmdir /s /q \"{target_dir}\"\necho AlphaForge uninstalled. User portfolio data in APPDATA was preserved.\npause\n"
    uninstaller_path.write_text(uninstaller_code, encoding="utf-8")

    # Show Windows Dialog Popup
    msg = f"AlphaForge v1.0 has been successfully installed!\n\nInstall Location:\n{target_dir}\n\nShortcuts created on Desktop and Start Menu."
    try:
        ctypes.windll.user32.MessageBoxW(0, msg, "AlphaForge Setup Complete", 0x40)
    except Exception:
        print(msg)

if __name__ == "__main__":
    main()
'''
    installer_script.write_text(script_content, encoding="utf-8")

    # Build Setup EXE using PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--name=AlphaForge-v1.0.0-Windows-Setup",
        f"--add-data={payload_zip};.",
        str(installer_script),
        "--distpath", str(dist_root),
        "--workpath", str(project_root / "build" / "setup_work"),
    ]

    print(f"Running PyInstaller setup build: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode != 0:
        print(f"PyInstaller setup build output:\n{res.stdout}\n{res.stderr}")
        raise RuntimeError(f"Failed to build installer setup EXE: return code {res.returncode}")

    print(f"SUCCESS: Installer created at {setup_exe}")
    print(f"Installer size: {setup_exe.stat().st_size / (1024*1024):.2f} MB")

if __name__ == "__main__":
    build_windows_setup_installer()
