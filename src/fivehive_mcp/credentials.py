import hashlib
import keyring

SERVICE = "fivehive-mcp"


def save_secret(profile: str, name: str, value: str) -> None:
    keyring.set_password(SERVICE, f"{profile}:{name}", value)


def load_secret(profile: str, name: str) -> str | None:
    return keyring.get_password(SERVICE, f"{profile}:{name}")


def delete_secret(profile: str, name: str) -> None:
    try:
        keyring.delete_password(SERVICE, f"{profile}:{name}")
    except keyring.errors.PasswordDeleteError:
        pass


def token_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
