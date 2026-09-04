param([ValidateSet('setup','run')][string]$Mode = 'run', [int]$Port = 8765, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$environmentPath = Join-Path $projectRoot '.conda-env'
Set-Location -LiteralPath $projectRoot

function Find-Conda {
    if ($env:CONDA_EXE -and (Test-Path -LiteralPath $env:CONDA_EXE)) { return $env:CONDA_EXE }
    $command = Get-Command conda.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $candidates = @("$env:USERPROFILE\miniconda3", "$env:USERPROFILE\anaconda3", "$env:USERPROFILE\miniforge3", "$env:ProgramData\miniconda3", "$env:ProgramData\anaconda3")
    $registry = Join-Path $env:USERPROFILE '.conda\environments.txt'
    if (Test-Path -LiteralPath $registry) { $candidates += Get-Content -LiteralPath $registry }
    foreach ($candidate in $candidates) {
        $executable = Join-Path $candidate 'Scripts\conda.exe'
        if (Test-Path -LiteralPath $executable) { return $executable }
    }
    throw 'Conda was not found. Install Miniforge or Miniconda, then retry from a Conda prompt (or set CONDA_EXE).'
}

try {
    $condaExecutable = Find-Conda
    if ($Mode -eq 'setup' -and !(Test-Path -LiteralPath (Join-Path $environmentPath 'python.exe'))) {
        & $condaExecutable create --prefix $environmentPath --override-channels -c conda-forge python=3.11 pip -y
        if ($LASTEXITCODE -ne 0) { throw 'Conda environment creation failed.' }
    }
    $pythonExecutable = Join-Path $environmentPath 'python.exe'
    if (!(Test-Path -LiteralPath $pythonExecutable)) { throw 'Environment not found. Run setup.bat first.' }
    $env:PATH = "$environmentPath;$environmentPath\Library\bin;$environmentPath\Scripts;$env:PATH"
    $env:PYTHONUTF8 = '1'
    & $pythonExecutable -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 11) else 1)'
    if ($LASTEXITCODE -ne 0) { throw 'This environment must use Python 3.11.' }
    if ($Mode -eq 'setup') {
        & $pythonExecutable -m pip install -c (Join-Path $projectRoot 'constraints.txt') (Join-Path $projectRoot 'aizynfinder') -e $projectRoot
        if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
        & $pythonExecutable -m pip check
        if ($LASTEXITCODE -ne 0) { throw 'Dependency consistency check failed.' }
        Write-Host 'Downloading public assets. Attribution and terms: docs/MODEL_DATA_SOURCES.md'
        & $pythonExecutable -m explorer.download
        if ($LASTEXITCODE -ne 0) { throw 'Data download failed. Re-run setup to retry.' }
        & $pythonExecutable -m explorer.setup_accessibility
        if ($LASTEXITCODE -ne 0) { throw "RAscore setup failed. Install Git and re-run setup to retry." }
        & $pythonExecutable -m explorer.diagnose
        if ($LASTEXITCODE -ne 0) { throw 'Diagnostics failed.' }
    } else {
        $launchArguments = @('-m', 'explorer.launcher', '--port', "$Port")
        if ($NoBrowser) { $launchArguments += '--no-browser' }
        & $pythonExecutable @launchArguments
        if ($LASTEXITCODE -ne 0) { throw 'Explorer could not start.' }
    }
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
