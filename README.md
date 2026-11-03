# FiveHive MCP

## Installation for WINDOWS
1. Run the commands in powershell:

If you don't have uv, install it:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

If you don't have python, install it:
```powershell
winget install -e --id Python.Python.3.13
```

In a new powershell window in the directory that it is installed:
```powershell
uv sync --extra test
uv run pytest tests
uv build
.\install.ps1 -Targets codex -WebsiteBaseUrl https://www.fivehive.org
```

2. Install the Google Drive plugin on codex, or the Google Drive and Google Docs connector on Claude or Google Drive and Google Docs customization for Antigravity. Google for installation guidance.

3. Restart your AI client or reconnect its MCP servers so it loads **fivehive-mcp**. The client starts the MCP automatically over stdio; you do not need to leave a separate terminal running or expose an MCP port.

4. Ask the AI to call `auth_status`, then `connect_website` if FiveHive is not connected. Open the returned verification URL, sign in through the normal FiveHive website, review the connection label, and select the courses this connection may access. Your website account must already have **member or admin** access; there is no separate MCP role.

5. Once you approve the connection in the browser, ask the AI to call `exchange_website` with the returned pairing ID, then check `auth_status` again. 


## Other clients and website environments

To detect supported clients and choose where to install, omit `-Targets`:

```powershell
.\install.ps1 -WebsiteBaseUrl https://www.fivehive.org
```

The installer detects Codex, Claude Desktop, and Antigravity configuration locations and asks which targets to register. You can also select `command-only` or provide a custom client's JSON configuration path. Registration support does not imply that every client's Google Drive connector has been tested.

For a separately running development website:

```powershell
.\install.ps1 -Targets codex -WebsiteBaseUrl http://127.0.0.1:10000
```

The configured website must have the FiveHive publishing API deployed under `/api/mcp/v1`. Setting its URL does not deploy or start that API. The website, Firebase configuration, and server credentials belong to the separate website deployment.

The installer writes `%LOCALAPPDATA%\fivehive-mcp\config.toml`. Set `website_base_url` there to the intended website. After switching environments, reconnect the MCP and pair with that website again; local and production accounts, content, and connections are separate.
