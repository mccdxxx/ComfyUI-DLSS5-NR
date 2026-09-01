param(
    [Parameter(Mandatory = $true)]
    [string]$Version
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Dist = Join-Path $Root 'dist'
$StageRoot = Join-Path $Dist 'stage'
$PackageName = 'ComfyUI-DLSS5-NR'
$Stage = Join-Path $StageRoot $PackageName

$bridge = Join-Path $Root 'native\bin\dlss5nr_bridge.dll'
$shim = Join-Path $Root 'runtime\caller\nvngx.dll_comfy.dll'
if (-not (Test-Path $bridge)) { throw "Missing built bridge: $bridge" }
if (-not (Test-Path $shim)) { throw "Missing built caller helper: $shim" }

Remove-Item -Recurse -Force $Dist -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $Stage | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Stage 'native\bin') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Stage 'runtime\caller') | Out-Null

$files = @(
    '__init__.py',
    'nodes.py',
    'requirements.txt',
    'README.md',
    'LICENSE',
    'THIRD_PARTY_NOTICES.md',
    'CHANGELOG.md',
    'diagnose_runtime.ps1',
    'diagnose_runtime.bat'
)
foreach ($rel in $files) {
    $src = Join-Path $Root $rel
    if (Test-Path $src) { Copy-Item $src (Join-Path $Stage $rel) -Force }
}
Copy-Item (Join-Path $Root 'runtime\README.txt') (Join-Path $Stage 'runtime\README.txt') -Force
Copy-Item $bridge (Join-Path $Stage 'native\bin\dlss5nr_bridge.dll') -Force
Copy-Item $shim (Join-Path $Stage 'runtime\caller\nvngx.dll_comfy.dll') -Force

# Safety gate: release assets must not contain NVIDIA proprietary runtimes.
$forbidden = @('_nvngx.dll', 'nvngx_dlssnr.dll', 'nvngx_dlss.dll')
foreach ($name in $forbidden) {
    $found = Get-ChildItem -Path $Stage -Filter $name -File -Recurse -ErrorAction SilentlyContinue
    if ($found) { throw "Refusing to package forbidden NVIDIA runtime: $($found.FullName)" }
}

$zip = Join-Path $Dist ("ComfyUI-DLSS5-NR-v{0}-windows-x64.zip" -f $Version)
Compress-Archive -Path $Stage -DestinationPath $zip -CompressionLevel Optimal
$hash = (Get-FileHash -Algorithm SHA256 $zip).Hash
$hashFile = $zip + '.sha256'
("{0}  {1}" -f $hash, (Split-Path -Leaf $zip)) | Set-Content -Path $hashFile -Encoding ascii

Write-Host "Release package: $zip"
Write-Host "SHA256: $hash"
