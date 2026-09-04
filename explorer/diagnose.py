"""Check dependencies, assets, model loading and local molecular rendering."""
import importlib.metadata
import json
from pathlib import Path
import platform
import sys


def main():
    if sys.version_info[:2] != (3, 11):
        raise RuntimeError("This release requires Python 3.11.")
    from explorer.chemistry import preview
    from explorer.download import ASSETS, valid
    root = Path(__file__).resolve().parent.parent
    for spec in ASSETS:
        if not spec.get("optional") and not valid(root / "data" / spec["filename"], spec):
            raise RuntimeError(f"Missing or corrupt asset: {spec['filename']}. Run setup again.")
    from explorer.accessibility import scores
    if scores("CCO")[1]["value"] is None:
        raise RuntimeError("RAscore model unavailable. Run setup again.")
    from aizynthfinder.aizynthfinder import AiZynthFinder
    finder = AiZynthFinder(configfile=str(root / "data" / "config.yml"))
    finder.expansion_policy.select("uspto")
    finder.filter_policy.select("uspto")
    finder.stock.select("zinc")
    print(json.dumps({"python": sys.version, "platform": platform.platform(),
                      "versions": {p: importlib.metadata.version(p) for p in ["aizynthfinder", "rdkit", "onnxruntime", "fastapi", "uvicorn"]},
                      "preview": preview("CCO")["canonical_smiles"], "stock_entries": len(finder.stock),
                      "model_loading": "passed"}, indent=2))


if __name__ == "__main__":
    main()
