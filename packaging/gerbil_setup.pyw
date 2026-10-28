#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerbil - installer (Gerbil_Setup.exe, built by build_exe.bat).
© 2026 Eloïs CHARBONNEL
Licence: GNU General Public License v3 or later (SPDX: GPL-3.0-or-later), see LICENSE.
This program comes with ABSOLUTELY NO WARRANTY; it is free software, and you are welcome to
redistribute it under the conditions of the licence.

One file to send: it holds the whole .exe version (Gerbil.zip) and installs it for the current user,
without administrator rights:
  - in %LOCALAPPDATA%\\Programs\\Gerbil (or another folder chosen in the window);
  - shortcuts in the Start menu and, if wanted, on the desktop;
  - an entry in Windows "Installed apps" (and Uninstall.bat in the folder) to remove it.
Installing again over an earlier version updates it; the AI models already downloaded ("models"
folder) are kept. Photos and results are never touched.

Test without building: py -3 gerbil_setup.pyw --zip dist\\Gerbil.zip
"""
import os
import re
import shutil
import subprocess
import sys
import threading
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP = "Gerbil"
PUBLISHER = "Eloïs CHARBONNEL"
FROZEN = getattr(sys, "frozen", False)
HERE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DIR = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "Programs", APP)
UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Gerbil"
MANIFEST = "installed_files.txt"         # top-level entries written by the installer (removed on update)
KEEP = {"models"}                        # downloaded by Gerbil itself: kept on update
PROGRAMS = ("Gerbil.exe", "gerbil_cli.exe")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

LAVENDER, LAVENDER_DARK, LAVENDER_PALE = "#A596D6", "#5B4D96", "#ECE8F7"
MINT, MINT_DARK = "#ABD6B4", "#2E7D4F"
WINDOW_BG, CARD_BG, TEXT, MUTED, RED = "#F6F4FB", "#FFFFFF", "#231C3A", "#6E6888", "#B03A3A"

UNINSTALL_BAT = r"""@echo off
REM Gerbil - uninstallation (written by Gerbil_Setup.exe)
title Gerbil - uninstallation
for %%P in (Gerbil.exe gerbil_cli.exe) do (
    tasklist /FI "IMAGENAME eq %%P" 2>nul | find /I "%%P" >nul && (
        echo Gerbil is open: close it, then uninstall again.
        pause
        exit /b 1
    )
)
echo Gerbil will be removed from this computer.
echo Your photos and results are not touched.
choice /M "Remove Gerbil"
if errorlevel 2 exit /b 0
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Gerbil.lnk" >nul 2>nul
powershell -NoProfile -Command "Remove-Item -LiteralPath (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Gerbil.lnk') -ErrorAction SilentlyContinue"
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\Gerbil" /f >nul 2>nul
cd /d "%TEMP%"
(goto) 2>nul & rmdir /s /q "%~dp0"
"""

SHORTCUTS_PS = r"""
$sh = New-Object -ComObject WScript.Shell
$exe = Join-Path $env:GERBIL_DIR 'Gerbil.exe'
$links = @(Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Gerbil.lnk')
if ($env:GERBIL_DESKTOP -eq '1') { $links += Join-Path ([Environment]::GetFolderPath('Desktop')) 'Gerbil.lnk' }
else { Remove-Item -LiteralPath (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Gerbil.lnk') -ErrorAction SilentlyContinue }
foreach ($l in $links) {
    $s = $sh.CreateShortcut($l)
    $s.TargetPath = $exe
    $s.WorkingDirectory = $env:GERBIL_DIR
    $s.IconLocation = "$exe,0"
    $s.Description = 'Gerbil - Archaeological photo toolkit'
    $s.Save()
}
"""


def version():
    for path in (os.path.join(HERE, "version.txt"), os.path.join(HERE, "..", "gerbil.py")):
        try:
            text = open(path, encoding="utf-8").read()
        except OSError:
            continue
        m = re.search(r'^VERSION = "([^"]+)"', text, re.M)
        return m.group(1) if m else text.strip()
    return ""


def payload():
    if "--zip" in sys.argv:
        return os.path.abspath(sys.argv[sys.argv.index("--zip") + 1])
    return os.path.join(HERE, "Gerbil.zip")


def running():
    """Gerbil programs open at the moment."""
    try:
        out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True,
                             creationflags=NO_WINDOW).stdout.lower()
    except OSError:
        return []
    return [p for p in PROGRAMS if f'"{p.lower()}"' in out]


def members(zf):
    """Files of the archive, without the top 'Gerbil' folder: [(info, relative path)]."""
    out = []
    for info in zf.infolist():
        parts = [p for p in info.filename.replace("\\", "/").split("/") if p]
        if parts and parts[0].lower() == APP.lower():
            parts = parts[1:]
        if not parts or ".." in parts or info.filename.endswith(("/", "\\")):
            continue
        out.append((info, os.path.join(*parts)))
    return out


def check_folder(folder):
    """None if the folder can receive Gerbil, otherwise the reason. A folder that already holds
    other things than Gerbil is refused: the update removes the previous program files."""
    if not os.path.exists(folder):
        return None
    if not os.path.isdir(folder):
        return "This is a file, not a folder."
    names = set(os.listdir(folder))
    if not names or "Gerbil.exe" in names or MANIFEST in names:
        return None
    return "This folder already holds other files: choose an empty folder, or a new one."


def install(folder, zip_path, desktop, progress):
    with zipfile.ZipFile(zip_path) as zf:
        files = members(zf)
        tops = {rel.split(os.sep)[0] for _, rel in files}
        old = set()
        try:
            with open(os.path.join(folder, MANIFEST), encoding="utf-8") as fh:
                old = {line.strip() for line in fh if line.strip()}
        except OSError:
            pass
        os.makedirs(folder, exist_ok=True)
        for name in (tops | old | {"Uninstall.bat"}) - KEEP:         # earlier version: removed first
            path = os.path.join(folder, name)
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.exists(path):
                os.remove(path)
        total = sum(i.file_size for i, _ in files) or 1
        done = 0
        for info, rel in files:
            dest = os.path.join(folder, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with zf.open(info) as src, open(dest, "wb") as dst:
                shutil.copyfileobj(src, dst, 1 << 20)
            done += info.file_size
            progress(0.95 * done / total)
    with open(os.path.join(folder, "Uninstall.bat"), "w", encoding="ascii", newline="\r\n") as fh:
        fh.write(UNINSTALL_BAT)
    with open(os.path.join(folder, MANIFEST), "w", encoding="utf-8") as fh:
        fh.write("\n".join(sorted(tops | {"Uninstall.bat", MANIFEST})) + "\n")
    env = dict(os.environ, GERBIL_DIR=folder, GERBIL_DESKTOP="1" if desktop else "0")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", SHORTCUTS_PS],
                   env=env, capture_output=True, creationflags=NO_WINDOW)
    register(folder, total)
    progress(1.0)


def register(folder, size):
    """Entry in Windows "Installed apps" (current user only)."""
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as k:
        exe = os.path.join(folder, "Gerbil.exe")
        for name, value in (("DisplayName", "Gerbil - Archaeological photo toolkit"),
                            ("DisplayVersion", version()), ("Publisher", PUBLISHER),
                            ("DisplayIcon", exe), ("InstallLocation", folder),
                            ("UninstallString", f'"{os.path.join(folder, "Uninstall.bat")}"')):
            winreg.SetValueEx(k, name, 0, winreg.REG_SZ, value)
        winreg.SetValueEx(k, "EstimatedSize", 0, winreg.REG_DWORD, int(size // 1024))
        winreg.SetValueEx(k, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(k, "NoRepair", 0, winreg.REG_DWORD, 1)


class Setup:
    def __init__(self, root):
        self.root = root
        root.title(f"Gerbil {version()} - Setup")
        root.configure(bg=WINDOW_BG)
        root.resizable(False, False)
        try:
            root.iconbitmap(os.path.join(HERE, "gerbil.ico"))
        except tk.TclError:
            pass
        st = ttk.Style(root)
        st.theme_use("clam")
        st.configure(".", background=WINDOW_BG, foreground=TEXT, font=("Segoe UI", 10))
        st.configure("Card.TFrame", background=CARD_BG)
        st.configure("Card.TLabel", background=CARD_BG)
        st.configure("Card.TCheckbutton", background=CARD_BG)
        st.configure("Title.TLabel", background=WINDOW_BG, foreground=LAVENDER_DARK, font=("Segoe UI", 16, "bold"))
        st.configure("Muted.TLabel", background=WINDOW_BG, foreground=MUTED)
        st.configure("Error.TLabel", background=CARD_BG, foreground=RED)
        st.configure("Run.TButton", background=MINT, foreground=TEXT, font=("Segoe UI", 11, "bold"), padding=(18, 6))
        st.map("Run.TButton", background=[("active", MINT_DARK), ("disabled", LAVENDER_PALE)],
               foreground=[("active", "#FFFFFF")])
        st.configure("TButton", background=LAVENDER_PALE, padding=(10, 4))
        st.configure("Horizontal.TProgressbar", background=LAVENDER, troughcolor=LAVENDER_PALE)

        head = ttk.Frame(root, padding=(18, 14, 18, 6))
        head.pack(fill="x")
        try:
            self.logo = tk.PhotoImage(file=os.path.join(HERE, "gerbil_64.png"))
            tk.Label(head, image=self.logo, bg=WINDOW_BG).pack(side="left", padx=(0, 12))
        except tk.TclError:
            pass
        titles = ttk.Frame(head)
        titles.pack(side="left")
        ttk.Label(titles, text="Gerbil", style="Title.TLabel").pack(anchor="w")
        ttk.Label(titles, text=f"Archaeological photo toolkit · version {version()} · © 2026 {PUBLISHER}",
                  style="Muted.TLabel").pack(anchor="w")

        card = ttk.Frame(root, style="Card.TFrame", padding=16)
        card.pack(fill="both", padx=18, pady=6)
        ttk.Label(card, text="Install in this folder:", style="Card.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        self.folder = tk.StringVar(value=DEFAULT_DIR)
        ttk.Entry(card, textvariable=self.folder, width=60).grid(row=1, column=0, sticky="ew", pady=4)
        ttk.Button(card, text="Browse…", command=self.browse).grid(row=1, column=1, padx=(6, 0))
        self.desktop = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, text="Shortcut on the desktop (and always in the Start menu)", variable=self.desktop,
                        style="Card.TCheckbutton").grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Label(card, text="No administrator rights needed. Installing over an earlier version updates it.",
                  style="Card.TLabel", foreground=MUTED).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.bar = ttk.Progressbar(card, maximum=1.0, length=420)
        self.bar.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        self.msg = tk.StringVar()
        ttk.Label(card, textvariable=self.msg, style="Error.TLabel", wraplength=520).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(6, 0))
        card.columnconfigure(0, weight=1)

        foot = ttk.Frame(root, padding=(18, 8, 18, 14))
        foot.pack(fill="x")
        self.go = ttk.Button(foot, text="Install", style="Run.TButton", command=self.start)
        self.go.pack(side="left")
        self.quit = ttk.Button(foot, text="Cancel", command=root.destroy)
        self.quit.pack(side="right")
        if not os.path.isfile(payload()):
            self.msg.set(f"The program files are missing ({payload()}).")
            self.go.state(["disabled"])

    def browse(self):
        d = filedialog.askdirectory(parent=self.root, initialdir=os.path.dirname(self.folder.get()) or None)
        if d:
            d = os.path.normpath(d)
            # a parent folder chosen: Gerbil goes in a "Gerbil" folder inside it
            self.folder.set(d if os.path.basename(d).lower() == "gerbil" else os.path.join(d, APP))

    def start(self):
        folder = os.path.normpath(os.path.expandvars(self.folder.get().strip()))
        reason = check_folder(folder) if folder else "Choose a folder."
        if reason:
            self.msg.set(reason)
            return
        while running():
            if not messagebox.askretrycancel("Gerbil is open",
                                             "Gerbil is open on this computer: close it, then click Retry.",
                                             parent=self.root):
                return
        self.msg.set("")
        self.go.state(["disabled"])
        self.quit.state(["disabled"])
        progress = lambda v: self.root.after(0, self.bar.configure, {"value": v})

        def work():
            try:
                install(folder, payload(), self.desktop.get(), progress)
                self.root.after(0, self.finished, folder, None)
            except Exception as e:
                self.root.after(0, self.finished, folder, f"{type(e).__name__}: {e}")
        threading.Thread(target=work, daemon=True).start()

    def finished(self, folder, error):
        self.quit.state(["!disabled"])
        if error:
            self.go.state(["!disabled"])
            self.msg.set("The installation failed: " + error)
            return
        self.msg.set("")
        self.quit.configure(text="Close")
        self.go.configure(text="Open Gerbil", command=lambda: self.launch(folder))
        self.go.state(["!disabled"])
        messagebox.showinfo("Gerbil", f"Gerbil is installed in\n{folder}\n\n"
                            "It is in the Start menu. To remove it: Windows Settings > Apps > Installed apps.",
                            parent=self.root)

    def launch(self, folder):
        env = dict(os.environ, PYINSTALLER_RESET_ENVIRONMENT="1")   # Gerbil starts afresh, not as part of the setup
        subprocess.Popen([os.path.join(folder, "Gerbil.exe")], cwd=folder, env=env)
        self.root.destroy()


def main():
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    Setup(root)
    root.mainloop()


if __name__ == "__main__":
    main()
