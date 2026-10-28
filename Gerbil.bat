@echo off
REM ==================================================================
REM  Gerbil - graphical interface
REM  (c) 2026 Elois CHARBONNEL - GPL-3.0-or-later (see LICENSE)
REM  Double-click to open the interface. Folders or photos dropped on
REM  this file are added to its list. Missing packages can be installed
REM  from the interface itself.
REM ==================================================================
set "PY=" & set "PYW="
py -3 -c "" >nul 2>nul && set "PY=py -3" && set "PYW=pyw -3"
if not defined PY python -c "" >nul 2>nul && set "PY=python" && set "PYW=pythonw"
if not defined PY (
    echo Python is not installed on this computer: double-click Install.bat first.
    pause
    exit /b 1
)
%PY% -c "import tkinter" >nul 2>nul
if errorlevel 1 (
    echo The tkinter module of Python is missing: reinstall Python from python.org
    echo keeping the "tcl/tk and IDLE" option ticked.
    pause
    exit /b 1
)
start "" %PYW% "%~dp0gerbil_gui.pyw" %*
