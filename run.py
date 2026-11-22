"""Entry point for Darya dental clinic app."""
import sys
import os
import time
import threading
import webbrowser
import uvicorn

PORT = 8765
URL = f"http://127.0.0.1:{PORT}"


def _open_browser():
    time.sleep(1.5)
    webbrowser.open(URL)


def main():
    threading.Thread(target=_open_browser, daemon=True).start()
    print(f"دریا در حال اجرا... {URL}")
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=PORT,
        log_level="warning",
        access_log=False,
    )


if __name__ == "__main__":
    main()
