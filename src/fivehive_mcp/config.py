from pathlib import Path
import os
import tomllib
from platformdirs import user_config_path, user_data_path
from pydantic import BaseModel


class Config(BaseModel):
    website_base_url: str = "http://localhost:3000"
    profile: str = "default"

    @property
    def data_dir(self) -> Path:
        path = user_data_path("fivehive-mcp") / self.profile
        path.mkdir(parents=True, exist_ok=True)
        return path


def load_config() -> Config:
    explicit = os.getenv("FIVEHIVE_MCP_CONFIG")
    # Keep the config location aligned with the Windows installer:
    # %LOCALAPPDATA%/fivehive-mcp/config.toml. platformdirs otherwise adds a
    # second application-author directory on Windows.
    path = Path(explicit) if explicit else user_config_path("fivehive-mcp", appauthor=False) / "config.toml"
    values: dict = {}
    if path.exists():
        values = tomllib.loads(path.read_text(encoding="utf-8-sig"))
    return Config.model_validate(values)
