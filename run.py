"""Convenient entrypoint to start the FastAPI app, similar to a Spring Boot main."""

import os

from app.env_loader import load_env
import uvicorn


def main() -> None:
    load_env()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload_enabled = os.getenv("RELOAD", "true").lower() == "true"

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload_enabled,
    )


if __name__ == "__main__":
    main()

