"""Pinned public assets with atomic downloads, checksums and provenance."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

import requests
import yaml
from explorer.engine import atomic_json

ASSETS = json.loads(Path(__file__).with_name("assets.json").read_text(encoding="utf-8"))


def digest(path, algorithm="md5"):
    hasher = hashlib.new(algorithm)
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def valid(path, spec):
    return path.is_file() and path.stat().st_size == spec["size"] and digest(path) == spec["md5"]


def download_asset(spec, folder):
    target = folder / spec["filename"]
    if valid(target, spec):
        print(f"Verified existing {target.name}", flush=True)
        return
    if shutil.disk_usage(folder).free < spec["size"] + 100_000_000:
        raise OSError(f"Insufficient disk space for {target.name}.")
    temporary = target.with_suffix(target.suffix + ".part")
    for attempt in range(3):
        try:
            print(f"Downloading {target.name} ({spec['size'] / 1e6:.1f} MB), attempt {attempt + 1}/3", flush=True)
            with requests.get(spec["url"], stream=True, timeout=(20, 60)) as response:
                response.raise_for_status()
                count = 0
                reported = -1
                with temporary.open("wb") as stream:
                    for chunk in response.iter_content(1024 * 1024):
                        count += len(chunk)
                        if count > spec["size"]:
                            raise ValueError(f"Unexpected download size for {target.name}.")
                        stream.write(chunk)
                        percent = int(100 * count / spec["size"])
                        if percent // 10 > reported:
                            print(f"  {target.name}: {percent}%", flush=True)
                            reported = percent // 10
            if not valid(temporary, spec):
                raise ValueError(f"Checksum or size mismatch for {target.name}.")
            temporary.replace(target)
            return
        except (requests.RequestException, OSError, ValueError):
            temporary.unlink(missing_ok=True)
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def setup_data(folder, include_optional=False):
    folder = Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    lock = folder / ".download.lock"
    try:
        handle = lock.open("x")
    except FileExistsError:
        raise RuntimeError("Another download may be running. If it stopped unexpectedly, remove data/.download.lock and retry.")
    try:
        handle.write(str(datetime.now(timezone.utc)))
        handle.close()
        selected = [s for s in ASSETS if include_optional or not s.get("optional")]
        for spec in selected:
            download_asset(spec, folder)
        manifest = {"retrieved_at": datetime.now(timezone.utc).isoformat(), "source_revision": "AiZynthFinder fork 8998736",
                    "changes": "File names normalized locally; file bytes unchanged.",
                    "assets": [{**s, "sha256": digest(folder / s["filename"], "sha256")} for s in selected]}
        atomic_json(folder / "manifest.json", manifest)
        config = {"expansion": {"uspto": [str(folder / "uspto_model.onnx"), str(folder / "uspto_templates.csv.gz")]},
                  "filter": {"uspto": str(folder / "uspto_filter_model.onnx")}, "stock": {"zinc": str(folder / "zinc_stock.hdf5")}}
        temp = folder / "config.yml.tmp"
        # ASCII YAML escapes also work with the vendored reader's Windows locale.
        temp.write_text(yaml.safe_dump(config, allow_unicode=False), encoding="utf-8")
        temp.replace(folder / "config.yml")
        print("Data verified. Configuration and provenance manifest saved.")
    finally:
        handle.close()
        lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=str(Path(__file__).resolve().parent.parent / "data"))
    parser.add_argument("--include-ringbreaker", action="store_true", help="Download optional upstream assets; the GUI uses USPTO.")
    args = parser.parse_args()
    try:
        setup_data(args.data_dir, args.include_ringbreaker)
    except Exception as exc:
        print(f"Setup failed: {exc}\nRe-run setup to retry. Verified downloads are reused.", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
