# -*- mode: python ; coding: utf-8 -*-
# PyInstaller recipe of the installer, dist\Gerbil_Setup.exe: one file holding dist\Gerbil.zip
# (run build_exe.bat rather than this file directly; dist\Gerbil.zip must exist).
import os
import re

HERE = os.path.abspath(SPECPATH)
ROOT = os.path.dirname(HERE)
ICON = os.path.join(ROOT, "icons", "gerbil.ico")
version = re.search(r'^VERSION = "([^"]+)"', open(os.path.join(ROOT, "gerbil.py"), encoding="utf-8").read(), re.M)
VERSION_FILE = os.path.join(ROOT, "build", "version.txt")
os.makedirs(os.path.dirname(VERSION_FILE), exist_ok=True)
with open(VERSION_FILE, "w", encoding="utf-8") as fh:
    fh.write(version.group(1))

a = Analysis([os.path.join(HERE, "gerbil_setup.pyw")], pathex=[HERE],
             datas=[(os.path.join(ROOT, "dist", "Gerbil.zip"), "."), (VERSION_FILE, "."),
                    (ICON, "."), (os.path.join(ROOT, "icons", "gerbil_64.png"), ".")],
             excludes=["numpy", "cv2", "PIL", "rawpy", "onnxruntime"])
EXE(PYZ(a.pure), a.scripts, a.binaries, a.datas, [], name="Gerbil_Setup", console=False, icon=ICON,
    upx=False)
