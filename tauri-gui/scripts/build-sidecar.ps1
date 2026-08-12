# Build the Python backend as a single-file executable and place it where
# Tauri expects the sidecar binary.

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path (Join-Path $PSScriptRoot "..") "..")
$BinaryDir = Join-Path (Join-Path (Join-Path $RepoRoot "tauri-gui") "src-tauri") "binaries"
$TargetName = "jlc2kicadlib-helper-x86_64-pc-windows-msvc.exe"

Push-Location $RepoRoot
try {
    Write-Host "Building sidecar with PyInstaller..."
    uv run pyinstaller `
        --onefile `
        --name jlc2kicadlib-helper `
        --clean `
        --copy-metadata JLC2KiCadLib `
        sidecar/jlc2kicadlib_helper.py

    New-Item -ItemType Directory -Force -Path $BinaryDir | Out-Null
    $Source = Join-Path (Join-Path $RepoRoot "dist") "jlc2kicadlib-helper.exe"
    $Destination = Join-Path $BinaryDir $TargetName

    Write-Host "Copying sidecar to $Destination"
    Copy-Item -Path $Source -Destination $Destination -Force

    Write-Host "Sidecar built successfully."
} finally {
    Pop-Location
}
