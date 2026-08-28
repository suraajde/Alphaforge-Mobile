r"""Windows Setup Installer Builder Script for AlphaForge (Sprint 14.1.10)

Generates a standalone, self-installing executable AlphaForge-v1.0.0-Windows-Setup.exe
from the compiled dist/AlphaForge-v1.0.0-Windows distribution directory.

Features:
- Automated Windows installer wizard with UAC Administrator elevation.
- Standard install directory: C:\Program Files\AlphaForge
- Creates Start Menu shortcut: "Start Menu\Programs\AlphaForge\AlphaForge.lnk"
- Creates Desktop shortcut: "Desktop\AlphaForge.lnk"
- Registers in Windows Settings -> Apps -> Installed apps / Add or Remove Programs
- Generates clean uninstaller script: "C:\Program Files\AlphaForge\uninstall.cmd"
- Preserves user portfolio data in %APPDATA%\AlphaForge\data upon uninstall.
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
import winreg
from pathlib import Path
import subprocess
import ctypes

def main():
    # Target directory: C:\Program Files\AlphaForge
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    target_dir = Path(program_files) / "AlphaForge"

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
    uninstaller_path = target_dir / "uninstall.cmd"

    # Create safe uninstaller script
    uninstaller_code = f"""@echo off
echo Uninstalling AlphaForge v1.0.0...
echo.

:: Remove Shortcuts
if exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\AlphaForge" rmdir /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\AlphaForge"
if exist "%PROGRAMDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\AlphaForge" rmdir /s /q "%PROGRAMDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\AlphaForge"
if exist "%USERPROFILE%\\Desktop\\AlphaForge.lnk" del /f /q "%USERPROFILE%\\Desktop\\AlphaForge.lnk"
if exist "%PUBLIC%\\Desktop\\AlphaForge.lnk" del /f /q "%PUBLIC%\\Desktop\\AlphaForge.lnk"
if exist "%USERPROFILE%\\OneDrive\\Desktop\\AlphaForge.lnk" del /f /q "%USERPROFILE%\\OneDrive\\Desktop\\AlphaForge.lnk"

:: Remove Windows Installed Apps Registry Entry
reg delete "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\AlphaForge" /f >nul 2>&1
reg delete "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\AlphaForge" /f >nul 2>&1

:: Remove Installation Directory
timeout /t 1 /nobreak >nul
cd /d %TEMP%
rmdir /s /q "{target_dir}" >nul 2>&1

echo.
echo AlphaForge v1.0.0 has been successfully uninstalled.
echo NOTE: User portfolio data in %APPDATA%\\AlphaForge\\data was preserved.
echo.
pause
"""
    uninstaller_path.write_text(uninstaller_code, encoding="utf-8")

    # Register in Windows Add or Remove Programs (Installed apps)
    reg_key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\AlphaForge"
    for root_hkey in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        try:
            with winreg.CreateKeyEx(root_hkey, reg_key_path, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "AlphaForge")
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "AlphaForge")
                winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(target_dir))
                winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{uninstaller_path}"')
                winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(exe_target))
                winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
                break
        except Exception:
            pass

    # Create Start Menu & Desktop Shortcuts
    try:
        app_data = os.environ.get("APPDATA", "")
        program_data = os.environ.get("ProgramData", "")
        user_profile = os.environ.get("USERPROFILE", "")

        targets = []
        if app_data:
            start_menu_dir = Path(app_data) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "AlphaForge"
            start_menu_dir.mkdir(parents=True, exist_ok=True)
            targets.append(start_menu_dir / "AlphaForge.lnk")

        if program_data:
            common_start_dir = Path(program_data) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "AlphaForge"
            try:
                common_start_dir.mkdir(parents=True, exist_ok=True)
                targets.append(common_start_dir / "AlphaForge.lnk")
            except Exception:
                pass

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
    except Exception:
        pass

    # Show Windows Dialog Popup
    msg = f"AlphaForge v1.0.0 has been successfully installed!\n\nInstall Location:\n{target_dir}\n\nShortcuts created on Desktop and Start Menu.\nRegistered in Windows Installed Apps."
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
        "--uac-admin",
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

    # Create Release ZIP Archive
    zip_target = dist_root / "AlphaForge-v1.0.0-Windows.zip"
    print(f"Creating release ZIP archive at {zip_target}...")
    if zip_target.exists():
        zip_target.unlink()
    shutil.make_archive(str(dist_root / "AlphaForge-v1.0.0-Windows"), 'zip', root_dir=dist_root, base_dir="AlphaForge-v1.0.0-Windows")

    print(f"SUCCESS: Installer created at {setup_exe}")
    print(f"Installer size: {setup_exe.stat().st_size / (1024*1024):.2f} MB")
    print(f"ZIP Archive created at {zip_target}")
    print(f"ZIP size: {zip_target.stat().st_size / (1024*1024):.2f} MB")

if __name__ == "__main__":
    build_windows_setup_installer()
