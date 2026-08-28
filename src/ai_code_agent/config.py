"""Environment-based application configuration."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str
    model: str = "auto"

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        public_url = os.getenv("UPSTREAM_PUBLIC_BASE_URL", "").strip()
        api_key = os.getenv("UPSTREAM_API_KEY", "").strip()
        model = os.getenv("UPSTREAM_MODEL", "auto").strip() or "auto"

        missing = [
            name
            for name, value in (
                ("UPSTREAM_PUBLIC_BASE_URL", public_url),
                ("UPSTREAM_API_KEY", api_key),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"Missing required environment variable(s): {', '.join(missing)}")

        base_url = public_url.rstrip("/")
        if not base_url.endswith("/v1"):
            base_url += "/v1"
        return cls(base_url=base_url, api_key=api_key, model=model)

