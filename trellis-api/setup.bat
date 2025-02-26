@echo off

if not defined RUN_MODE (
    for %%I in ("%~dp0..") do set "ADDON_DIR=%%~fI"
    for %%A in ("%~dp0.") do set "TRELLIS_API_DIR=%%~fA"
    set "VENV_PATH=%ADDON_DIR%\venv\trellis-api"
    set "PYTHON311_FOLDER=%ADDON_DIR%\portable_tools\python311"
    set "TRELLIS-API-VENV-WHEEL_DIR=%ADDON_DIR%\portable_tools\trellis-api-venv-wheel"
)

set PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple
set PYTHONNOUSERSITE=1
set CONDA_PREFIX=
set CONDA_PYTHON_EXE=
set CONDA_DEFAULT_ENV=
set CONDA_SHLVL=
set CONDAPATH=
set PYTHONPATH=
set PYTHONHOME=
set PIP_DISABLE_PIP_VERSION_CHECK=1
set PIP_NO_CACHE_DIR=off


if exist "%TRELLIS_API_DIR%\trellis_dep_manifest.txt" (
    echo [Trellis Setup] All Trellis dependencies already manifest 1>&2
    echo [Trellis Setup] Progress: 100%% 1>&2
    set "PATH=%VENV_PATH%\Scripts;%PATH%"
) else (
    if exist "%VENV_PATH%" (
        echo [Trellis Setup] Deleting a existing legacy venv folder 1>&2
        rmdir /s /q "%VENV_PATH%" 2>&1
        if errorlevel 1 (
            echo [Trellis Setup] Deleting a existing legacy venv folder failed 1>&2
            exit 1
        )
    )
    echo [Trellis Setup] Creating venv... 1>&2
    echo [Trellis Setup] Progress: 10%% 1>&2
    "%PYTHON311_FOLDER%\python.exe" -m virtualenv "%VENV_PATH%" 2>&1
    if errorlevel 1 (
        rmdir /s /q "%VENV_PATH%" 2>&1
        echo [Trellis Setup] Creating venv failed 1>&2
        exit 1
    )

    echo [Trellis Setup] Coping pip.ini in python_embed folder to venv folder... 1>&2
    echo [Trellis Setup] Progress: 15%% 1>&2
    copy /Y "%PYTHON311_FOLDER%\pip.ini" "%VENV_PATH%\pip.ini" 2>&1
    if errorlevel 1 (
        @REM rmdir /s /q "%VENV_PATH%" 2>&1
        echo [Trellis Setup] Coping pip.ini in python_embed folder to venv folder failed 1>&2
        exit 1
    )

    echo [Trellis Setup] Activating venv... 1>&2
    echo [Trellis Setup] Progress: 20%% 1>&2
    set "PATH=%VENV_PATH%\Scripts;%PATH%"
    if errorlevel 1 (
        rmdir /s /q "%VENV_PATH%" 2>&1
        echo [Trellis Setup] Activating venv failed 1>&2
        exit 1
    )

    echo [Trellis Setup] Installing requirements from requirements.txt to venv... 1>&2
    echo [Trellis Setup] Progress: 30%% 1>&2
    python -m pip install -r "%TRELLIS_API_DIR%\requirements.txt" 2>&1
    if errorlevel 1 (
        rmdir /s /q "%VENV_PATH%" 2>&1
        echo [Trellis Setup] Installing requirements from requirements.txt to venv failed 1>&2
        exit 1
    )

    echo [Trellis Setup] Installing torch with cuda118 compiled... 1>&2
    echo [Trellis Setup] Progress: 40%% 1>&2
    python -m pip install https://mirrors.aliyun.com/pytorch-wheels/cu118/torch-2.1.2+cu118-cp311-cp311-win_amd64.whl 2>&1
    if errorlevel 1 (
        rmdir /s /q "%VENV_PATH%" 2>&1
        echo [Trellis Setup] Installing torch with cuda118 compiled failed 1>&2
        exit 1
    )
    
    echo [Trellis Setup] Installing torchaudio with cuda118 compiled... 1>&2
    echo [Trellis Setup] Progress: 45%% 1>&2
    python -m pip install https://mirrors.aliyun.com/pytorch-wheels/cu118/torchaudio-2.1.2+cu118-cp311-cp311-win_amd64.whl 2>&1
    if errorlevel 1 (
        rmdir /s /q "%VENV_PATH%" 2>&1
        echo [Trellis Setup] Installing torchaudio with cuda118 compiled failed 1>&2
        exit 1
    )

    echo [Trellis Setup] Installing torchvision with cuda118 compiled... 1>&2
    echo [Trellis Setup] Progress: 50%% 1>&2
    python -m pip install https://mirrors.aliyun.com/pytorch-wheels/cu118/torchvision-0.16.2+cu118-cp311-cp311-win_amd64.whl 2>&1
    if errorlevel 1 (
        rmdir /s /q "%VENV_PATH%" 2>&1
        echo echo [Trellis Setup] Installing torchvision with cuda118 compiled failed 1>&2
        exit 1
    )

    echo [Trellis Setup] Installing xformers with cuda118 compiled... 1>&2
    echo [Trellis Setup] Progress: 55%% 1>&2
    python -m pip install https://mirrors.aliyun.com/pytorch-wheels/cu118/xformers-0.0.23.post1+cu118-cp311-cp311-win_amd64.whl 2>&1
    if errorlevel 1 (
        rmdir /s /q "%VENV_PATH%" 2>&1
        echo [Trellis Setup] Installing xformers with cuda118 compiled failed 1>&2
        exit 1
    )

    echo [Trellis Setup] Installing utils3d with cuda118 compiled... 1>&2
    echo [Trellis Setup] Progress: 60%% 1>&2
    python -m pip install "%TRELLIS-API-VENV-WHEEL_DIR%\utils3d-0.0.2-py3-none-any.whl" 2>&1
    if errorlevel 1 (
        rmdir /s /q "%VENV_PATH%" 2>&1
        echo [Trellis Setup] Installing utils3d with cuda118 compiled failed 1>&2
        exit 1
    )

    echo [Trellis Setup] Installing kaolin with cuda118 compiled... 1>&2
    echo [Trellis Setup] Progress: 65%% 1>&2
    rem Install kaolin
    (
        python -m pip install "%TRELLIS-API-VENV-WHEEL_DIR%\warp_lang-1.5.1+cu11-py3-none-win_amd64.whl"
        python -m pip install "%TRELLIS-API-VENV-WHEEL_DIR%\kaolin-0.17.0-cp311-cp311-win_amd64.whl"
    ) 2>&1
    if errorlevel 1 (
        rmdir /s /q "%VENV_PATH%" 2>&1
        echo [Trellis Setup] Installing kaolin with cuda118 compiled failed 1>&2
        exit 1
    )

    echo [Trellis Setup] Installing nvdiffrast with cuda118 compiled... 1>&2
    echo [Trellis Setup] Progress: 70%% 1>&2
    python -m pip install "%TRELLIS-API-VENV-WHEEL_DIR%\nvdiffrast-0.3.3-cp311-cp311-win_amd64.whl" 2>&1
    if errorlevel 1 (
        rmdir /s /q "%VENV_PATH%" 2>&1
        echo [Trellis Setup] Installing nvdiffrast with cuda118 compiled failed 1>&2
        exit 1
    )

    echo [Trellis Setup] Installing diffoctreerast with cuda118 compiled... 1>&2
    echo [Trellis Setup] Progress: 75%% 1>&2
    python -m pip install "%TRELLIS-API-VENV-WHEEL_DIR%\diffoctreerast-0.0.0-cp311-cp311-win_amd64.whl" 2>&1
    if errorlevel 1 (
        rmdir /s /q "%VENV_PATH%" 2>&1
        echo [Trellis Setup] Installing diffoctreerast with cuda118 compiled? failed 1>&2
        exit 1
    )

    echo [Trellis Setup] Installing diff_gaussian_rasterization with cuda118 compiled... 1>&2
    echo [Trellis Setup] Progress: 80%% 1>&2
    python -m pip install "%TRELLIS-API-VENV-WHEEL_DIR%\diff_gaussian_rasterization-0.0.0-cp311-cp311-win_amd64.whl" 2>&1
    if errorlevel 1 (
        rmdir /s /q "%VENV_PATH%" 2>&1
        echo [Trellis Setup] Installing diff_gaussian_rasterization with cuda118 compiledfailed 1>&2
        exit 1
    )

    echo [Trellis Setup] Downloading Trellis-image-large, dinov2, birefnet model files... 1>&2
    echo [Trellis Setup] Progress: 90%% 1>&2
    (
        modelscope download --model zhiliaomatters/TRELLIS-image-large --local_dir "%VENV_PATH%\TRELLIS-image-large"
        modelscope download --model zhiliaomatters/facebookresearch-dinov2 --local_dir "%VENV_PATH%\facebookresearch_dinov2"
        modelscope download --model zhiliaomatters/danielgatis-rembg birefnet-general-lite.onnx --local_dir "%VENV_PATH%\rembg"
    ) 2>&1
    if errorlevel 1 (
        rmdir /s /q "%VENV_PATH%" 2>&1
        echo [Trellis Setup] Downloading Trellis-image-large, dinov2, birefnet model files failed 1>&2
        exit 1
    )

    echo [Trellis Setup] Creating dependencies manifest flag file... 1>&2
    echo [Trellis Setup] Progress: 100%% 1>&2
    echo "Trellis dependencies manifest" > "%TRELLIS_API_DIR%\trellis_dep_manifest.txt" 2>&1
    if errorlevel 1 (
        rmdir /s /q "%VENV_PATH%" 2>&1
        echo [Trellis Setup] Creating dependencies manifest flag file failed 1>&2
        exit 1
    )
)
