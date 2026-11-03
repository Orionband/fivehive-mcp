import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError
from fivehive_mcp.website_client import checked_json


def test_structured_api_error_reaches_mcp_without_headers_or_response_secrets():
    response = httpx.Response(409, json={"error": {"code": "REVISION_CONFLICT", "message": "private-source-url"}, "requestId": "request-123"}, request=httpx.Request("POST", "https://example.org/api", headers={"Authorization": "Bearer private-token"}))
    with pytest.raises(ToolError) as error:
        checked_json(response)
    assert "REVISION_CONFLICT" in str(error.value)
    assert "request-123" in str(error.value)
    assert "private-token" not in str(error.value)
    assert "private-source-url" not in str(error.value)


def test_unstructured_server_failure_is_actionable_without_exposing_html():
    with pytest.raises(ToolError) as error:
        checked_json(httpx.Response(500, text="<html>private internal details</html>"))
    assert "HTTP 500" in str(error.value)
    assert "private internal details" not in str(error.value)
