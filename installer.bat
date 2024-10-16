@echo off
setlocal

REM Check if Python is available
where python >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in the PATH.
    echo Please install Python to use this script.
    pause
    exit /b
)

pip install torch
python -m pip install --upgrade pip

REM Run Python script to check CUDA version
python check_cuda_version.py

REM Read CUDA version from the file
set /p CUDA_VERSION=<cuda_version.txt

IF "%CUDA_VERSION%"=="None" (
    echo CUDA is not available. Please ensure CUDA is properly installed.
    pause
    exit /b
)

echo Detected CUDA Version: %CUDA_VERSION%

REM Ensure CUDA version does not exceed 12.1
for /f "tokens=1-2 delims=." %%a in ("%CUDA_VERSION%") do (
    set CUDA_MAJOR=%%a
    set CUDA_MINOR=%%b
)

IF %CUDA_MAJOR% GEQ 12 (
    IF %CUDA_MINOR% GTR 1 (
        set CUDA_VERSION=12.1
    )
)

REM Construct CUDA version string
set CUDA_VERSION_SHORT=%CUDA_MAJOR%%CUDA_MINOR%
echo Using CUDA Version: %CUDA_VERSION_SHORT%

REM Check if the correct version of PyTorch is installed
pip show torch | findstr "Version:" | findstr "cu%CUDA_VERSION_SHORT%" >nul
IF %ERRORLEVEL% NEQ 0 (
    echo Installing PyTorch with CUDA %CUDA_VERSION_SHORT% support...
    pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu%CUDA_VERSION_SHORT%
) ELSE (
    echo PyTorch with CUDA %CUDA_VERSION_SHORT% support is already installed.
)

pip install numpy
pip install mss
pip install PyQt5
pip install pynput
echo Installation completed!
pause