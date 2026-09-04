"""Spawn-safe computation entry point. All heavy model state lives in the child."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import traceback
from datetime import datetime, timezone


def atomic_json(path, data):
    path = Path(path)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=_json_default, allow_nan=False), encoding="utf-8")
    temp.replace(path)


def _json_default(value):
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def search_worker(config_path, request, output_dir):
    output = Path(output_dir)
    try:
        for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
            os.environ[name] = "1"
        atomic_json(output / "phase.json", {"phase": "Loading models and stock"})
        from aizynthfinder.aizynthfinder import AiZynthFinder
        from explorer.trees import summarize
        finder = AiZynthFinder(configfile=config_path)
        finder.expansion_policy.select("uspto")
        finder.filter_policy.select("uspto")
        finder.stock.select("zinc")
        finder.config.search.time_limit = request["search_seconds"]
        finder.config.search.iteration_limit = request["iterations"]
        finder.config.search.max_transforms = request["max_transforms"]
        finder.target_smiles = request["smiles"]
        finder.prepare_tree()
        atomic_json(output / "phase.json", {"phase": "Searching retrosynthetic routes"})
        from explorer.search import search
        stats = search(finder, request.get("solved_route_target", 0),
                       lambda count: atomic_json(output / "phase.json", {"phase": f"Searching · {count} distinct solved routes found"}))
        atomic_json(output / "phase.json", {"phase": "Ranking routes"})
        from aizynthfinder.analysis.utils import RouteSelectionArguments
        limit = request.get("return_routes", 25)
        finder.build_routes(selection=RouteSelectionArguments(nmin=limit, nmax=limit))
        routes = finder.routes.dict_with_extra(include_scores=True, include_metadata=True)[:limit]
        versions = {p: importlib.metadata.version(p) for p in ("retrosynthesis-explorer", "aizynthfinder", "rdkit", "onnxruntime", "reaction-utils", "rdchiral", "numpy")}
        versions["python"] = platform.python_version()
        manifest = Path(config_path).with_name("manifest.json")
        from explorer.accessibility import scores
        ra_manifest = Path(config_path).with_name("rascore-xgb.provenance.json")
        result = {"target_accessibility": scores(request["smiles"]),
                  "rascore_provenance": json.loads(ra_manifest.read_text(encoding="utf-8")) if ra_manifest.exists() else None,
                  "search_stats": stats, "returned_routes": len(routes), "request": request,
                  "created_at": datetime.now(timezone.utc).isoformat(),
                  "versions": versions, "platform": platform.platform(), "stock": "zinc",
                  "config_sha256": hashlib.sha256(Path(config_path).read_bytes()).hexdigest(),
                  "data_manifest": json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else None,
                  "solved_definition": "All terminal molecules are available in the selected stock.",
                  "score_note": "Search scores are ranking heuristics, not synthesis success probabilities.",
                  "routes": routes, "summaries": [summarize(r, i) for i, r in enumerate(routes)]}
        atomic_json(output / "result.json", result)
    except Exception as exc:
        (output / "error.log").write_text(traceback.format_exc(), encoding="utf-8")
        atomic_json(output / "failure.json", {"error": f"Search failed: {type(exc).__name__}: {exc}"})
