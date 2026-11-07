# -*- mode: python ; coding: utf-8 -*-
# PyInstaller recipe of the Gerbil .exe version (run build_exe.bat rather than this file directly).
# Two programs sharing the same libraries, in dist\Gerbil\ :
#   Gerbil.exe      the interface (no console window)
#   gerbil_cli.exe  the processing engine (console; folders can be dropped on it)
import os

HERE = os.path.abspath(SPECPATH)
ICON = os.path.join(HERE, "icons", "gerbil.ico")
icons = [(os.path.join(HERE, "icons", f), "icons")
         for f in ("gerbil.ico", "gerbil_64.png", "gerbil_96.png", "gerbil_128.png")]
fonts = [(os.path.join(HERE, "fonts", f), "fonts") for f in os.listdir(os.path.join(HERE, "fonts"))
         if f.endswith((".ttf", ".txt"))]                # interface fonts (SIL Open Font License)

gui = Analysis([os.path.join(HERE, "gerbil_gui.pyw")], pathex=[HERE], datas=icons + fonts,
               hiddenimports=["onnxruntime"])   # numpy, OpenCV, Pillow, onnxruntime: review (one click), plates…
engine = Analysis([os.path.join(HERE, "gerbil.py")], pathex=[HERE],
                  hiddenimports=["onnxruntime"], excludes=["tkinter", "matplotlib", "IPython"])

gui_exe = EXE(PYZ(gui.pure), gui.scripts, [], exclude_binaries=True, name="Gerbil",
              console=False, icon=ICON, upx=False)
engine_exe = EXE(PYZ(engine.pure), engine.scripts, [], exclude_binaries=True, name="gerbil_cli",
                 console=True, icon=ICON, upx=False)

COLLECT(gui_exe, gui.binaries, gui.datas, engine_exe, engine.binaries, engine.datas,
        name="Gerbil", upx=False)
