$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    python -m venv (Join-Path $projectRoot ".venv")
}

& $venvPython -m pip install -r (Join-Path $projectRoot "requirements.txt")

$pythonBase = & $venvPython -c "import sys; print(sys.base_prefix)"
$tclDir = Join-Path $pythonBase "tcl\tcl8.6"
$tkDir = Join-Path $pythonBase "tcl\tk8.6"

if (-not (Test-Path $tclDir)) {
    throw "Could not find Tcl data directory: $tclDir"
}

if (-not (Test-Path $tkDir)) {
    throw "Could not find Tk data directory: $tkDir"
}

$pyinstaller = Join-Path $projectRoot ".venv\Scripts\pyinstaller.exe"

& $pyinstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name AngelsOnlineHelper `
    --icon (Join-Path $projectRoot "angel.ico") `
    --version-file (Join-Path $projectRoot "version_info.txt") `
    --add-data "image;image" `
    --add-data "my_model.onnx;." `
    --add-data "angel.ico;." `
    --add-data "$tclDir;_tcl_data" `
    --add-data "$tkDir;_tk_data" `
    (Join-Path $projectRoot "Game.py")

Write-Host "Executable built at: $(Join-Path $projectRoot 'dist\AngelsOnlineHelper.exe')"
