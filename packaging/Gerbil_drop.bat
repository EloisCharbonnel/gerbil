@echo off
REM ==================================================================
REM  Gerbil (.exe version) - drag and drop
REM  Drag and drop one or more photo folders (or photos) onto this file.
REM  The results go into an "outlined_result" subfolder next to the
REM  photos. Settings: add options to the "set OPTIONS=" line below
REM  (right-click this file > Edit), for example --background white
REM  Full list of options: double-click this file.
REM ==================================================================
set OPTIONS=--open

if "%~1"=="" (
    "%~dp0gerbil_cli.exe" --help
) else (
    "%~dp0gerbil_cli.exe" %* %OPTIONS%
)
pause
