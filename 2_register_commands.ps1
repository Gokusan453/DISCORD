# ============================================================
#  Registers the slash commands with Discord.
#  No Python needed - PowerShell ships with Windows.
#
#  Right-click this file -> "Run with PowerShell"
# ============================================================

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host ""
Write-Host "=== Registering slash commands with Discord ===" -ForegroundColor Cyan
Write-Host ""

# --- read .env ----------------------------------------------------
if (-not (Test-Path ".env")) {
    Write-Host "[X] No .env found in this folder." -ForegroundColor Red
    Read-Host "Press Enter to close"; exit 1
}

$env_vars = @{}
Get-Content ".env" | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
        $i = $line.IndexOf("=")
        $env_vars[$line.Substring(0, $i).Trim()] = $line.Substring($i + 1).Trim().Trim('"')
    }
}

$token  = $env_vars["DISCORD_BOT_TOKEN"]
$app_id = $env_vars["DISCORD_APP_ID"]

if (-not $token) {
    Write-Host "[X] DISCORD_BOT_TOKEN is missing from .env" -ForegroundColor Red
    Write-Host "    Get it here: Developer Portal -> Bot -> Reset Token"
    Read-Host "Press Enter to close"; exit 1
}
if (-not $app_id) { $app_id = "1548832028055838780" }

# --- ask for the server ID ----------------------------------------
Write-Host "Paste your server ID (right-click server name -> Copy Server ID)."
Write-Host "Leave empty = all servers (can take up to an hour)."
$guild = (Read-Host "Server ID").Trim()

if ($guild) {
    $url = "https://discord.com/api/v10/applications/$app_id/guilds/$guild/commands"
    $scope = "server $guild"
} else {
    $url = "https://discord.com/api/v10/applications/$app_id/commands"
    $scope = "all servers"
}

# --- load and send the commands -----------------------------------
if (-not (Test-Path "commands.json")) {
    Write-Host "[X] commands.json is missing from this folder." -ForegroundColor Red
    Read-Host "Press Enter to close"; exit 1
}
$body = Get-Content "commands.json" -Raw -Encoding UTF8

Write-Host ""
Write-Host "Sending to Discord ($scope)..." -ForegroundColor Yellow

# Discord and Cloudflare block browser-like user agents (error 40333).
# A bot has to identify itself like this, per the docs:
$ua = "DiscordBot (https://github.com/Gokusan453/DISCORD, 1.0)"

try {
    $result = Invoke-RestMethod -Uri $url -Method Put -Body $body `
        -ContentType "application/json; charset=utf-8" `
        -UserAgent $ua `
        -Headers @{ Authorization = "Bot $token" }

    Write-Host ""
    Write-Host "Success! $($result.Count) commands registered:" -ForegroundColor Green
    foreach ($c in $result) { Write-Host "   /$($c.name)  -  $($c.description)" }
    Write-Host ""
    if ($guild) {
        Write-Host "They are live in that server NOW. Type / in a channel." -ForegroundColor Green
    } else {
        Write-Host "Global commands can take up to an hour to appear." -ForegroundColor Yellow
    }
}
catch {
    Write-Host ""
    Write-Host "[X] Discord returned an error:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message }
    Write-Host ""
    Write-Host "What it usually means:" -ForegroundColor Yellow
    Write-Host "  401            -> wrong DISCORD_BOT_TOKEN (reset it, update .env)"
    Write-Host "  403 code 50001 -> the app is not in that server (open the invite link)"
    Write-Host "  403 code 40333 -> Cloudflare blocked the request; just try again"
    Write-Host "  404            -> wrong server ID or app ID"
}

Write-Host ""
Read-Host "Press Enter to close"
