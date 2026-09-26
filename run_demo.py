"""
VinBank AI Guardrails & Red-Team Demo Runner
Launches the FastAPI server and opens the interactive dashboard in your browser.
"""
import sys
import webbrowser
from pathlib import Path

# Add src and current directory
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn

if __name__ == "__main__":
    url = "http://127.0.0.1:8000"
    print("=" * 60)
    print("Starting VinBank AI Guardrails Interactive Demo...")
    print(f"Opening browser at: {url}")
    print("=" * 60)

    # Open browser automatically after a short delay
    import threading
    import time

    def open_browser():
        time.sleep(1.2)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run("web_demo.app:app", host="127.0.0.1", port=8000, reload=False)
