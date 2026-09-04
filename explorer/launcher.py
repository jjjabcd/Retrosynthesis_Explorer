"""Reserve the loopback port, reuse an existing instance, open after readiness."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import threading
import time
import urllib.request
import webbrowser


def instance_id():
    return hashlib.sha256(str(Path(__file__).resolve().parent.parent).encode()).hexdigest()[:16]


def existing_instance(port):
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f"http://127.0.0.1:{port}/api/health", timeout=1) as response:
            data = json.load(response)
            return data.get("app") == "retrosynthesis-explorer" and data.get("instance_id") == instance_id()
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Port must be between 1024 and 65535.")
    url = f"http://127.0.0.1:{args.port}"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Windows needs exclusive address use; do not use SO_REUSEADDR there.
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        sock.bind(("127.0.0.1", args.port))
        sock.listen(128)
    except OSError:
        sock.close()
        if existing_instance(args.port):
            print(f"Explorer is already running at {url}")
            if not args.no_browser:
                webbrowser.open(url)
            return
        parser.exit(1, f"Port {args.port} is occupied. Use --port with another port, e.g. --port 8766.\n")
    import uvicorn
    from explorer.server import create_app
    server = uvicorn.Server(uvicorn.Config(create_app(), host="127.0.0.1", port=args.port, workers=1))

    def open_when_ready():
        for _ in range(200):
            if server.should_exit:
                return
            if server.started and existing_instance(args.port):
                webbrowser.open(url)
                return
            time.sleep(0.1)

    if not args.no_browser:
        threading.Thread(target=open_when_ready, daemon=True).start()
    print(f"Starting Explorer at {url}. Press Ctrl+C to stop.", flush=True)
    try:
        server.run(sockets=[sock])
    finally:
        sock.close()


if __name__ == "__main__":
    main()
