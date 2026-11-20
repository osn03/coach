# One-command setup for the Adaptive Endurance Coach (Windows / PowerShell 5.1+).
#
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
#
# What it does (safe to re-run; re-running also updates the installed skill):
#   1. Installs uv if missing (uv also fetches Python 3.12 automatically)
#   2. Installs the Intervals.icu MCP server's dependencies
#   3. Asks for your Intervals.icu API key + athlete ID, tests them, writes intervals-mcp-server\.env
#   4. Copies the coaching skill to %USERPROFILE%\.claude\skills\
#   5. Registers the MCP server with Claude Code (if installed), else prints the Claude Desktop config

$ErrorActionPreference = 'Stop'
$Root      = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerDir = Join-Path $Root 'intervals-mcp-server'
$SkillSrc  = Join-Path $Root 'adaptive-endurance-coach\skills\adaptive-endurance-coach'
$SkillsDir = Join-Path $env:USERPROFILE '.claude\skills'
$EnvFile   = Join-Path $ServerDir '.env'

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "    $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "    $msg" -ForegroundColor Yellow }

# --- 1. uv -------------------------------------------------------------------
Step 'Checking for uv'
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Warn 'uv not found - installing it'
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        throw 'uv installed but not on PATH. Open a new terminal and run this script again.'
    }
}
$Uv = (Get-Command uv).Source
Ok "uv: $Uv"

# --- 2. server dependencies --------------------------------------------------
Step 'Installing MCP server dependencies (uv sync)'
Push-Location $ServerDir
try { & $Uv sync --python 3.12; if ($LASTEXITCODE -ne 0) { throw 'uv sync failed' } }
finally { Pop-Location }
Ok 'Dependencies installed'

# --- 3. credentials ----------------------------------------------------------
Step 'Intervals.icu credentials'
$writeEnv = $true
if (Test-Path $EnvFile) {
    $ans = Read-Host '    intervals-mcp-server\.env already exists. Keep it? [Y/n]'
    if ($ans -eq '' -or $ans -match '^[Yy]') { $writeEnv = $false; Ok 'Keeping existing .env' }
}
if ($writeEnv) {
    Write-Host '    Find both at https://intervals.icu/settings -> Developer Settings.'
    do {
        $AthleteId = (Read-Host '    Athlete ID (e.g. i123456)').Trim()
        if ($AthleteId -match '^\d+$') { $AthleteId = "i$AthleteId" }
    } until ($AthleteId -match '^i\d+$')
    $sec = Read-Host '    API key (input hidden)' -AsSecureString
    $ApiKey = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)).Trim()

    $auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("API_KEY:$ApiKey"))
    try {
        $me = Invoke-RestMethod -Uri "https://intervals.icu/api/v1/athlete/$AthleteId" `
              -Headers @{ Authorization = "Basic $auth" } -TimeoutSec 20
        Ok "Connected to Intervals.icu as: $($me.name)"
    } catch {
        Warn "Could not verify credentials ($($_.Exception.Message))."
        $ans = Read-Host '    Save them anyway? [y/N]'
        if ($ans -notmatch '^[Yy]') { throw 'Aborted. Check the API key and athlete ID and re-run.' }
    }
    @(
        '# Intervals.icu credentials - never commit this file (it is gitignored)'
        "API_KEY=$ApiKey"
        "ATHLETE_ID=$AthleteId"
    ) | Set-Content -Path $EnvFile -Encoding ASCII
    Ok "Wrote $EnvFile"
}

# --- 4. skill ----------------------------------------------------------------
Step 'Installing the coaching skill'
New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null
$dest = Join-Path $SkillsDir 'adaptive-endurance-coach'
if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
Copy-Item -Recurse -Force $SkillSrc $dest
Ok "Installed to $dest (SKILL.md + references/)"

# --- 5. register MCP server --------------------------------------------------
Step 'Registering the Intervals.icu MCP server'
$args_ = @('run', '--directory', $ServerDir, 'python', 'src/intervals_mcp_server/server.py')
if (Get-Command claude -ErrorAction SilentlyContinue) {
    & claude mcp remove intervals --scope user *> $null
    & claude mcp add intervals --scope user -- $Uv @args_
    if ($LASTEXITCODE -eq 0) { Ok "Registered 'intervals' with Claude Code (user scope)" }
    else { Warn 'claude mcp add failed - see the README for manual registration.' }
} else {
    Warn 'Claude Code CLI not found. For Claude Desktop, add this to claude_desktop_config.json under "mcpServers":'
    $cfg = @{ intervals = @{ command = $Uv; args = $args_ } } | ConvertTo-Json -Depth 4
    Write-Host $cfg
}

Write-Host "`nDone. Restart Claude, then say: 'I want to start training for <your goal>'." -ForegroundColor Green
