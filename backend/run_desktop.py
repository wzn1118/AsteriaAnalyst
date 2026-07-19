from __future__ import annotations

import os
import threading
import time
import webbrowser

import uvicorn


def open_browser(url: str) -> None:
    time.sleep(1.2)
    webbrowser.open(url)


def should_open_browser() -> bool:
    flag = (os.getenv("ASTERIA_OPEN_BROWSER", "1") or "1").strip().lower()
    return flag not in {"0", "false", "no", "off"}


def build_launch_url(host: str, port: int) -> str:
    launch_path = (os.getenv("ASTERIA_LAUNCH_PATH", "/revision") or "/revision").strip()
    if not launch_path.startswith("/"):
        launch_path = f"/{launch_path}"
    return f"http://{host}:{port}{launch_path}"


def main() -> None:
    host = os.getenv("ASTERIA_HOST", "127.0.0.1")
    port = int(os.getenv("ASTERIA_PORT", "8787"))
    url = build_launch_url(host, port)
    if should_open_browser():
        threading.Thread(target=open_browser, args=(url,), daemon=True).start()
    uvicorn.run("app.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
