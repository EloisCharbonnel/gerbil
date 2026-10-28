@echo off
REM ==================================================================
REM  Gerbil - installation (once per computer)
REM  (c) 2026 Elois CHARBONNEL - GPL-3.0-or-later (see LICENSE)
REM  Installs the Python packages Gerbil needs (numpy, OpenCV,
REM  Pillow, rawpy) and, if wanted, the AI second opinion (onnxruntime).
REM  If Python itself is missing, offers to install it with winget.
REM  (Not needed for the .exe version.)
REM ==================================================================
title Gerbil - installation
set "PY="
py -3 -c "" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "" >nul 2>nul && set "PY=python"
if defined PY goto packages

echo Python is not installed on this computer.
echo.
where winget >nul 2>nul
if errorlevel 1 goto manual
set "ANSWER="
set /p "ANSWER=Install Python 3.13 now with winget, the Windows installer? [Y/N] "
if /i "%ANSWER%"=="Y" goto winget
if /i "%ANSWER%"=="O" goto winget
goto manual

:winget
winget install -e --id Python.Python.3.13 --scope user
echo.
echo When the Python installation is finished, close this window and
echo double-click Install.bat again to install the packages.
pause
exit /b 0

:manual
echo Install Python from https://www.python.org/downloads/
echo keeping the "py launcher" option ticked, then double-click Install.bat again.
pause
exit /b 1

:packages
%PY% "%~dp0gerbil_gui.pyw" --install
echo.
pause
