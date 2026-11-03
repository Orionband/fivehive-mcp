[CmdletBinding()]
param(
  [ValidateSet("stdio", "sse", "streamable-http")]
  [string]$Transport = "stdio"
)

$ErrorActionPreference = "Stop"
if (Get-Command fivehive-mcp -ErrorAction SilentlyContinue) {
  if ($Transport -eq "stdio") { fivehive-mcp; exit $LASTEXITCODE }
  throw "The MCP is installed for stdio. The website API is the HTTP service; MCP transport remains stdio by design."
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw "uv is required." }
uv run --project $PSScriptRoot fivehive-mcp
