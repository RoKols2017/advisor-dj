param(
    [Parameter(Mandatory = $true)]
    [string]$SourceDir,

    [Parameter(Mandatory = $true)]
    [string]$TargetDir,

    [Parameter(Mandatory = $true)]
    [string]$SourceId,

    [string]$Pattern = "*.json",
    [int]$MaxRetry = 5,
    [int]$RetryDelaySeconds = 10,
    [string]$LogPath = "C:\\ProgramData\\Advisor\\logs\\send_to_advisor_inbox.log"
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)
    $timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
    New-Item -Path (Split-Path -Parent $LogPath) -ItemType Directory -Force | Out-Null
    Add-Content -Path $LogPath -Value "$timestamp $Message"
}

if (-not (Test-Path -LiteralPath $SourceDir)) {
    Write-Log "source=$SourceId status=error reason=missing_source path=$SourceDir"
    exit 1
}

New-Item -Path $TargetDir -ItemType Directory -Force | Out-Null

$files = Get-ChildItem -LiteralPath $SourceDir -File -Filter $Pattern

foreach ($file in $files) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $safeName = "${SourceId}_$timestamp`_$($file.Name)"
    $tmpName = "$safeName.part"
    $tmpTarget = Join-Path $TargetDir $tmpName
    $finalTarget = Join-Path $TargetDir $safeName

    $attempt = 1
    $copied = $false

    while ($attempt -le $MaxRetry -and -not $copied) {
        try {
            Copy-Item -LiteralPath $file.FullName -Destination $tmpTarget -Force
            Move-Item -LiteralPath $tmpTarget -Destination $finalTarget -Force
            $copied = $true
            Write-Log "source=$SourceId status=sent file=$($file.Name) target=$safeName"
        }
        catch {
            Write-Log "source=$SourceId status=retry file=$($file.Name) attempt=$attempt error=$($_.Exception.Message)"
            Start-Sleep -Seconds $RetryDelaySeconds
            $attempt += 1
        }
    }

    if (-not $copied) {
        Write-Log "source=$SourceId status=failed file=$($file.Name)"
    }
}
