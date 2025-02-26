@echo off

rem Set default values
set PRECISION=float16
set DEVICE=dynamic
set REINSTALL=false
set RUN_MODE=true

rem Check if arguments are passed
if "%~1" == "--precision" set PRECISION=%~2
if "%~3" == "--device" set DEVICE=%~4
if "%~5" == "--reinstall" set REINSTALL=%~6

for %%I in ("%~dp0..") do set "ADDON_DIR=%%~fI"
for %%A in ("%~dp0.") do set "TRELLIS_API_DIR=%%~fA"
set "VENV_PATH=%ADDON_DIR%\venv\trellis-api"
set "PYTHON311_FOLDER=%ADDON_DIR%\portable_tools\python311"
set "TRELLIS-API-VENV-WHEEL_DIR=%ADDON_DIR%\portable_tools\trellis-api-venv-wheel"
set "SETUP_SCRIPT_PATH=%TRELLIS_API_DIR%\setup.bat"

if "%REINSTALL%"=="true" (
    echo [Trellis Setup] User request reinstallation of Trellis 1>&2
    echo [Trellis Setup] Deleting trellis_dep_manifest file and venv folder 1>&2
    (
        del /f "%TRELLIS_API_DIR%trellis_dep_manifest.txt"
        rmdir /s /q "%VENV_PATH%"
    ) 2>&1
    if errorlevel 1 (
        echo [Trellis Setup] Deleting trellis_dep_manifest file and venv folder failed 1>&2
        exit 1
    )
)

call "%SETUP_SCRIPT_PATH%"
if errorlevel 1 (
    echo [Trellis Setup] Trellis Setup failed. Exit...
    exit 1
)

echo [Trellis Launching] Launching Trellis generator... 1>&2
python "%TRELLIS_API_DIR%\main.py" --precision %PRECISION% --device %DEVICE%
if errorlevel 1 (
    exit 1
)

