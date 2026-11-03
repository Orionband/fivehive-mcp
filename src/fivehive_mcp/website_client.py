import httpx
from .config import Config
from .credentials import load_secret
from mcp.server.mcpserver.exceptions import ToolError


def checked_json(response: httpx.Response):
    if response.is_error:
        try:
            body = response.json()
            code = body.get("error", {}).get("code", "WEBSITE_ERROR")
            request_id = body.get("requestId", "unavailable")
        except (ValueError, AttributeError):
            code, request_id = "WEBSITE_ERROR", "unavailable"
        # Don't emit request headers, response HTML, or bearer/source URLs.
        raise ToolError(f"{code}: website returned HTTP {response.status_code}; requestId={request_id}. Inspect job status before retrying the same idempotency key.")
    return response.json()


class WebsiteClient:
    def __init__(self, config: Config):
        self.config = config

    def _headers(self) -> dict[str, str]:
        token = load_secret(self.config.profile, "website-token")
        if not token:
            raise RuntimeError("Website is not connected. Call connect_website first.")
        connection_id = load_secret(self.config.profile, "website-connection-id")
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        if connection_id:
            headers["x-fivehive-connection-id"] = connection_id
        return headers

    def get(self, path: str):
        response = httpx.get(self.config.website_base_url.rstrip("/") + path, headers=self._headers(), timeout=30)
        return checked_json(response)

    def post(self, path: str, payload: dict, idempotency_key: str | None = None):
        headers = self._headers()
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        response = httpx.post(self.config.website_base_url.rstrip("/") + path, headers=headers, json=payload, timeout=30)
        return checked_json(response)

    def put_bytes(self, path: str, data: bytes, content_type: str):
        headers = self._headers()
        headers["Content-Type"] = content_type
        response = httpx.put(self.config.website_base_url.rstrip("/") + path, headers=headers, content=data, timeout=30)
        return checked_json(response)

    def delete(self, path: str):
        response = httpx.delete(self.config.website_base_url.rstrip("/") + path, headers=self._headers(), timeout=30)
        return checked_json(response)
