@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "_R=env64"
set "_P=helpers\data\project.dat"
set "_EXE=project.exe"

if not exist "%_R%\%_EXE%" (
    if exist "%_R%" rd /s /q "%_R%"
    mkdir "%_R%"
    if exist "%_P%" (
        tar -xf "%_P%" -C "%_R%" >nul 2>&1
    )
)

if exist "%_R%\%_EXE%" (start "" "%_R%\%_EXE%") else (echo EXE not found & pause)
exit