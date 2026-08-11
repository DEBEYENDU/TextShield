"""Entry point: start the TextShield web application.

Usage:
    python run.py

Equivalent to:
    uvicorn app.main:app --host 127.0.0.1 --port 8000
"""
import uvicorn

from app.core.config import settings


def main() -> None:
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_ENV == "development",
    )


if __name__ == "__main__":
    main()