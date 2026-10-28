@echo off
REM ==================================================================
REM  Builds the Gerbil .exe version, for computers without Python:
REM    dist\Gerbil\Gerbil.exe      the interface
REM    dist\Gerbil\gerbil_cli.exe  the processing engine
REM    dist\Gerbil_Setup.exe       the installer: the one file to send
REM    dist\Gerbil.zip             the same, to unzip by hand
REM  Python is needed on THIS computer only. Run it again after each
REM  change of the scripts. First run: about 5 minutes (downloads).
REM  The new version is built aside (build\dist) and replaces
REM  dist\Gerbil only once it is complete.
REM ==================================================================
title Gerbil - building the .exe version
cd /d "%~dp0"
for %%P in (Gerbil.exe gerbil_cli.exe) do (
    tasklist /FI "IMAGENAME eq %%P" 2>nul | find /I "%%P" >nul && (
        echo %%P is running: close it, then run build_exe.bat again.
        pause
        exit /b 1
    )
)
set "PY="
py -3 -c "" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "" >nul 2>nul && set "PY=python"
if not defined PY (
    echo Python is needed to build the .exe version: double-click Install.bat first.
    pause
    exit /b 1
)
set "VENV=%~dp0build\venv"
if not exist "%VENV%\Scripts\python.exe" (
    echo Creating the build environment...
    %PY% -m venv "%VENV%" || goto failed
)
"%VENV%\Scripts\python.exe" -m pip install --disable-pip-version-check --upgrade -r requirements.txt onnxruntime-directml pyinstaller || goto failed
"%VENV%\Scripts\python.exe" -m PyInstaller --noconfirm --clean --distpath build\dist --workpath build\pyinstaller gerbil.spec || goto failed
copy /y README.md build\dist\Gerbil\ >nul
copy /y docs\PSEUDOCODE.txt build\dist\Gerbil\ >nul
copy /y packaging\Gerbil_drop.bat build\dist\Gerbil\ >nul

REM replace the previous version only now
if not exist dist mkdir dist
if exist dist\Gerbil rmdir /s /q dist\Gerbil
if exist dist\Gerbil (
    echo dist\Gerbil could not be replaced: a file in it is open, an Explorer window or Gerbil.exe.
    echo The new version is in build\dist\Gerbil.
    goto failed
)
move build\dist\Gerbil dist\Gerbil >nul || goto failed
if exist dist\Gerbil.zip del dist\Gerbil.zip
powershell -NoProfile -Command "Compress-Archive -Path 'dist\Gerbil' -DestinationPath 'dist\Gerbil.zip'" || goto failed
REM installer: one file holding Gerbil.zip
if exist dist\Gerbil_Setup.exe del dist\Gerbil_Setup.exe
"%VENV%\Scripts\python.exe" -m PyInstaller --noconfirm --distpath dist --workpath build\pyinstaller_setup packaging\gerbil_setup.spec || goto failed
echo.
echo Done: dist\Gerbil_Setup.exe (to send), dist\Gerbil\Gerbil.exe and dist\Gerbil.zip
pause
exit /b 0

:failed
echo.
echo The build failed: see the messages above.
pause
exit /b 1
