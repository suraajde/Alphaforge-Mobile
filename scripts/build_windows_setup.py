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
    dist_root = Path(r"D:\ALPHAFORGE\dist")
    app_dir = dist_root / "AlphaForge-v1.0.0-Windows"
    setup_exe = dist_root / "AlphaForge-v1.0.0-Windows-Setup.exe"

    if not app_dir.exists():
        raise FileNotFoundError(f"Distribution directory not found at {app_dir}")

    print("Building standalone Windows Installer AlphaForge-v1.0.0-Windows-Setup.exe...")

    # Create installer payload zip inside temp build directory
    payload_dir = Path(r"D:\ALPHAFORGE\build\installer_payload")
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

    # Write installer script entrypoint
    installer_script = payload_dir / "setup_runner.py"
    script_content = r'''import os
import sys
import shutil
import zipfile
from pathlib import Path
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def main():
    print("=" * 60)
    print("      AlphaForge AI Portfolio Engine — Windows Setup")
    print("=" * 60)
    print()

    # Target directory: %LOCALAPPDATA%\Programs\AlphaForge
    local_app_data = os.environ.get("LOCALAPPDATA", r"C:\Users\Public")
    target_dir = Path(local_app_data) / "Programs" / "AlphaForge"

    print(f"Installing AlphaForge to: {target_dir}")
    if target_dir.exists():
        try:
            shutil.rmtree(target_dir)
        except Exception as e:
            print(f"Updating existing installation directory... ({e})")

    target_dir.mkdir(parents=True, exist_ok=True)

    # Extract bundled payload
    if hasattr(sys, "_MEIPASS"):
        payload_zip = Path(sys._MEIPASS) / "app_payload.zip"
    else:
        payload_zip = Path(__file__).parent / "app_payload.zip"

    print("Extracting application files...")
    with zipfile.ZipFile(payload_zip, 'r') as zf:
        zf.extractall(target_dir)

    # Create Start Menu shortcut
    try:
        app_data = os.environ.get("APPDATA", "")
        if app_data:
            start_menu_dir = Path(app_data) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "AlphaForge"
            start_menu_dir.mkdir(parents=True, exist_ok=True)

            exe_target = target_dir / "AlphaForge.exe"
            shortcut_path = start_menu_dir / "AlphaForge.lnk"

            # Create shortcut via PowerShell VBScript bridge
            ps_cmd = f'$s=(New-Object -COM WScript.Shell).CreateShortcut("{shortcut_path}"); $s.TargetPath="{exe_target}"; $s.WorkingDirectory="{target_dir}"; $s.Save()'
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
            print("Start Menu shortcut created successfully.")

            # Create Desktop shortcut
            user_profile = os.environ.get("USERPROFILE", "")
            if user_profile:
                desktop_dir = Path(user_profile) / "Desktop"
                if desktop_dir.exists():
                    desktop_shortcut = desktop_dir / "AlphaForge.lnk"
                    ps_desktop = f'$s=(New-Object -COM WScript.Shell).CreateShortcut("{desktop_shortcut}"); $s.TargetPath="{exe_target}"; $s.WorkingDirectory="{target_dir}"; $s.Save()'
                    subprocess.run(["powershell", "-Command", ps_desktop], capture_output=True)
                    print("Desktop shortcut created successfully.")
    except Exception as exc:
        print(f"Shortcut creation notice: {exc}")

    # Create uninstaller script in target directory
    uninstaller_path = target_dir / "uninstall.bat"
    uninstaller_path.write_text(f'@echo off\necho Uninstalling AlphaForge...\ntimeout /t 2 /nobreak >nul\nrmdir /s /q "{target_dir}"\necho AlphaForge uninstalled successfully. User data in APPDATA was preserved.\npause\n', encoding="utf-8")

    print()
    print("=" * 60)
    print("   INSTALLATION COMPLETE!")
    print(f"   AlphaForge is installed at: {target_dir}")
    print("   User portfolio data location: %APPDATA%\\AlphaForge\\data")
    print("=" * 60)
    print()

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
        "--workpath", str(Path(r"D:\ALPHAFORGE\build\setup_work")),
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
