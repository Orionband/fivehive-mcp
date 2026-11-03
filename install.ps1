[CmdletBinding()]
param(
  [string]$WebsiteBaseUrl = "http://127.0.0.1:10000",
  [switch]$WithTests,
  [string[]]$Targets
)

$ErrorActionPreference = "Stop"
$McpRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Executable = Join-Path $env:USERPROFILE ".local\bin\fivehive-mcp.exe"
$CodexConfig = Join-Path $env:USERPROFILE ".codex\config.toml"
$ClaudeConfig = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
$AntigravityConfig = Join-Path $env:USERPROFILE ".gemini\config\mcp_config.json"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  throw "uv is required. Install it from https://docs.astral.sh/uv/getting-started/installation/ and rerun this script."
}

if ($WithTests) {
  uv tool install --force --editable $McpRoot --with pytest --with respx
} else {
  uv tool install --force --editable $McpRoot
}
if ($LASTEXITCODE -ne 0) { throw "Installing fivehive-mcp failed." }

$configDir = Join-Path $env:LOCALAPPDATA "fivehive-mcp"
New-Item -ItemType Directory -Force -Path $configDir | Out-Null
$configPath = Join-Path $configDir "config.toml"
@"
website_base_url = "$WebsiteBaseUrl"
profile = "default"
"@ | Set-Content -LiteralPath $configPath -Encoding UTF8

function Add-CodexRegistration {
  $section = "[mcp_servers.fivehive-mcp]`ncommand = '$Executable'`nargs = []`ncwd = '$McpRoot'`nstartup_timeout_sec = 30.0`n"
  if (-not (Test-Path $CodexConfig)) { New-Item -ItemType File -Force -Path $CodexConfig | Out-Null }
  $existing = Get-Content -LiteralPath $CodexConfig -Raw
  Copy-Item -LiteralPath $CodexConfig -Destination "$CodexConfig.bak" -Force
  if ($existing -match '(?m)^\[mcp_servers\.fivehive-mcp\]') {
    $pattern = '(?ms)^\[mcp_servers\.fivehive-mcp\]\r?\n.*?(?=^\[|\z)'
    $updated = [regex]::Replace($existing, $pattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($match) $section + "`n" })
  } else { $updated = $existing + "`n" + $section }
  Set-Content -LiteralPath $CodexConfig -Value $updated -Encoding UTF8
  Write-Host "Registered FiveHive MCP in Codex: $CodexConfig"
}

function Add-JsonRegistration([string]$Path, [string]$ClientName) {
  $parent = Split-Path -Parent $Path
  New-Item -ItemType Directory -Force -Path $parent | Out-Null
  $root = if (Test-Path $Path) {
    $raw = Get-Content -LiteralPath $Path -Raw
    if ([string]::IsNullOrWhiteSpace($raw)) { [pscustomobject]@{} } else { $raw | ConvertFrom-Json }
  } else { [pscustomobject]@{} }
  if (-not ($root.PSObject.Properties.Name -contains "mcpServers")) { $root | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{}) }
  $server = [pscustomobject]@{ command = $Executable; args = @(); cwd = $McpRoot }
  $existing = $root.mcpServers.PSObject.Properties.Name
  if ($existing -contains "fivehive-mcp") { $root.mcpServers.PSObject.Properties.Remove("fivehive-mcp") }
  $root.mcpServers | Add-Member -NotePropertyName "fivehive-mcp" -NotePropertyValue $server
  if (Test-Path $Path) { Copy-Item -LiteralPath $Path -Destination "$Path.bak" -Force }
  $root | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $Path -Encoding UTF8
  Write-Host "Registered FiveHive MCP in ${ClientName}: $Path"
}

function Detect-Targets {
  $found = @()
  if ((Test-Path $CodexConfig) -or (Get-Command codex -ErrorAction SilentlyContinue)) { $found += "codex" }
  if ((Test-Path $ClaudeConfig) -or (Get-Command claude -ErrorAction SilentlyContinue)) { $found += "claude" }
  if ((Test-Path $AntigravityConfig) -or (Get-Command antigravity -ErrorAction SilentlyContinue)) { $found += "antigravity" }
  return $found
}

if (-not $Targets -or $Targets.Count -eq 0) {
  $detected = Detect-Targets
  Write-Host "Detected MCP clients: $(if ($detected.Count) { $detected -join ', ' } else { 'none' })"
  Write-Host "Install target options: codex, claude, antigravity, command-only, custom"
  $answer = Read-Host "Install for which target(s)? Enter comma-separated values (default: detected clients, or codex)"
  if ([string]::IsNullOrWhiteSpace($answer)) { $Targets = if ($detected.Count) { $detected } else { @('codex') } }
  else { $Targets = $answer.Split(',') | ForEach-Object { $_.Trim().ToLowerInvariant() } | Where-Object { $_ } }
}

foreach ($target in $Targets) {
  switch ($target) {
    "codex" { Add-CodexRegistration }
    "claude" { Add-JsonRegistration -Path $ClaudeConfig -ClientName "Claude Desktop" }
    "antigravity" { Add-JsonRegistration -Path $AntigravityConfig -ClientName "Google Antigravity" }
    "command-only" { Write-Host "Installed the command only; no client config was changed." }
    "custom" {
      $customPath = Read-Host "Enter the JSON config path for the custom MCP client"
      Add-JsonRegistration -Path $customPath -ClientName "custom client"
    }
    default { throw "Unknown install target '$target'. Choose codex, claude, antigravity, command-only, or custom." }
  }
}

Write-Host "Installed fivehive-mcp globally through uv."
Write-Host "Config: $configPath"
Write-Host "Run: fivehive-mcp"
Write-Host "Source setup for Codex: run /plugins, search for Google Drive, install it, and connect the Google account when prompted."
