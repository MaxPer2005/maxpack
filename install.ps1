param(
    [string]$InstallDir = "$env:LOCALAPPDATA\\Programs\\maxpack"
)

$ErrorActionPreference = "Stop"

$repo = "MaxPer2005/maxpack"
$binaryName = "maxpack.exe"
$checksumsName = "SHA256SUMS.txt"

$arch = $env:PROCESSOR_ARCHITECTURE
if (-not $arch) {
    $arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
}

switch -Regex ($arch) {
    "^(AMD64|x86_64|X64)$" { $asset = "maxpack-windows-amd64.exe" }
    default {
        throw "Current release supports only Windows x86_64. See https://github.com/$repo/releases/latest for manual downloads."
    }
}

$downloadUrl = "https://github.com/$repo/releases/latest/download/$asset"
$checksumsUrl = "https://github.com/$repo/releases/latest/download/$checksumsName"

$tmpDir = Join-Path $env:TEMP ("maxpack-install-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tmpDir | Out-Null

try {
    $tmpBinary = Join-Path $tmpDir $asset
    $tmpSums = Join-Path $tmpDir $checksumsName

    Invoke-WebRequest -Uri $downloadUrl -OutFile $tmpBinary
    Invoke-WebRequest -Uri $checksumsUrl -OutFile $tmpSums

    $expectedLine = Select-String -Path $tmpSums -Pattern ("  " + [regex]::Escape($asset) + "$") | Select-Object -First 1
    if (-not $expectedLine) {
        throw "Checksum entry for $asset not found."
    }

    $expected = ($expectedLine.Line -split "\s+")[0].ToLowerInvariant()
    $actual = (Get-FileHash -Path $tmpBinary -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected) {
        throw "Checksum verification failed for $asset."
    }

    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
    $dest = Join-Path $InstallDir $binaryName
    Copy-Item $tmpBinary $dest -Force

    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if (-not $userPath) {
        $userPath = ""
    }
    $segments = $userPath -split ";" | Where-Object { $_ }
    if ($segments -notcontains $InstallDir) {
        $newPath = if ($userPath) { "$userPath;$InstallDir" } else { $InstallDir }
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Host ""
        Write-Host "NOTE: Added $InstallDir to your user PATH. Open a new terminal if 'maxpack' is not found yet."
        Write-Host ""
    }

    Write-Host "Installed maxpack to $dest"
    & $dest --version
}
finally {
    Remove-Item -Recurse -Force $tmpDir -ErrorAction SilentlyContinue
}
