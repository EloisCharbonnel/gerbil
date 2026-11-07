@echo off
REM ==================================================================
REM  Gerbil - drag and drop
REM  Drag and drop one or more photo folders (or photos) onto this file.
REM  The results go into an "outlined_result" subfolder next to the
REM  photos.
REM
REM  Settings: add options to the "set OPTIONS=" line below
REM  (right-click this file > Edit), for example:
REM    set OPTIONS=--open --background white
REM    set OPTIONS=--open --no-original-layer
REM    set OPTIONS=--open --remove-putty
REM    set OPTIONS=--open --ai          (AI second opinion, see docs\MANUAL.md)
REM  Full list of options: double-click this file.
REM  First use on a computer: missing packages are installed (once).
REM ==================================================================
set OPTIONS=--open

set "PY="
py -3 -c "" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "" >nul 2>nul && set "PY=python"
if not defined PY (
    echo Python is not installed on this computer: double-click Install.bat first.
    pause
    exit /b 1
)
%PY% "%~dp0gerbil_gui.pyw" --check >nul 2>nul
if errorlevel 1 (
    %PY% "%~dp0gerbil_gui.pyw" --install
    if errorlevel 1 (
        pause
        exit /b 1
    )
)

if "%~1"=="" (
    %PY% "%~dp0gerbil.py" --help
) else (
    %PY% "%~dp0gerbil.py" %* %OPTIONS%
)
pause
