$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtime = Join-Path $root 'runtime'
$nr = Join-Path $runtime 'nvngx_dlssnr.dll'
$core = Join-Path $runtime '_nvngx.dll'
$shimNew = Join-Path $runtime 'caller\nvngx.dll_comfy.dll'
$shimOld = Join-Path $runtime 'caller\nvngx.dll'

function Show-Dll([string]$label, [string]$path) {
    Write-Host ""
    Write-Host "[$label] $path"
    if (-not (Test-Path $path)) { Write-Host '  MISSING' -ForegroundColor Yellow; return }
    $f = Get-Item $path
    Write-Host "  Size: $($f.Length) bytes"
    Write-Host "  Modified: $($f.LastWriteTime)"
    try { Write-Host "  FileVersion: $($f.VersionInfo.FileVersion)" } catch {}
    try { Write-Host "  SHA256: $((Get-FileHash $path -Algorithm SHA256).Hash)" } catch {}
    try {
        $sig = Get-AuthenticodeSignature $path
        Write-Host "  Signature: $($sig.Status)"
        if ($sig.SignerCertificate) { Write-Host "  Signer: $($sig.SignerCertificate.Subject)" }
    } catch {}
}

Write-Host '[DLSS5-NR] Runtime diagnostics v0.2.0'
Show-Dll 'NGX core local override (optional)' $core
Show-Dll 'DLSS NR user-supplied runtime' $nr
if (Test-Path $shimNew) { Show-Dll 'Project caller helper' $shimNew } else { Show-Dll 'Project caller helper (legacy)' $shimOld }

Write-Host ""
Write-Host 'Note: absence of runtime\_nvngx.dll is normal; the bridge can discover NGX core from the NVIDIA DriverStore.'
