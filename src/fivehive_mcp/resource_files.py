from pathlib import Path

PACKAGE = Path(__file__).parent
PROJECT_ROOT = PACKAGE.parents[1]


def resource_text(name: str) -> str:
    bundled = PACKAGE / "resources" / name
    if bundled.is_file():
        return bundled.read_text(encoding="utf-8")
    if name == "porting-reference.md":
        path = PROJECT_ROOT / "docs" / "google-docs-porting-reference.md"
    elif name.startswith("schemas/"):
        path = PROJECT_ROOT / name
    else:
        raise FileNotFoundError(f"Required MCP resource unavailable: {name}")
    return path.read_text(encoding="utf-8")
