"""Fetch a pinned, intentionally isolated clone and prepare its public RA model."""
import hashlib
import json
import io
from pathlib import Path
import pickle
import subprocess

from explorer.accessibility import ROOT, MODEL, fingerprint

REPOSITORY = "https://github.com/reymond-group/RAscore.git"
COMMIT = "cb77db503ee5cbf0e8bb8963df6e5b76b3a94f06"
SHA256 = "7ca8461207e76ded1224f393e7bdb21973b5c6caece2a4e550e6396efe2cf9f7"


class LegacyLabelEncoder:
    """Unused classifier label metadata; booster inference bypasses this wrapper."""
    pass


class ModelUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) == ("xgboost.compat", "XGBoostLabelEncoder"):
            return LegacyLabelEncoder
        return super().find_class(module, name)


def main():
    import xgboost as xgb
    folder = ROOT / "external" / "RAscore"
    if not folder.exists():
        folder.parent.mkdir(exist_ok=True)
        subprocess.run(["git", "clone", REPOSITORY, str(folder)], check=True)
        subprocess.run(["git", "-C", str(folder), "checkout", "--detach", COMMIT], check=True)
    # Never overwrite an existing clone or load an unverified pickle.
    source = folder / "RAscore/models/XGB_chembl_ecfp_counts/model.pkl"
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise RuntimeError("RAscore model does not match the pinned source. Existing clone left unchanged.")
    booster = ModelUnpickler(io.BytesIO(data)).load().get_booster()
    booster.set_param({"nthread": 1})
    MODEL.parent.mkdir(exist_ok=True)
    temporary = MODEL.with_name("rascore-xgb.tmp.json")
    temporary.write_bytes(booster.save_raw(raw_format="json"))
    restored = xgb.Booster(params={"nthread": 1})
    restored.load_model(bytearray(temporary.read_bytes()))
    # Published upstream examples check the legacy-pickle compatibility adapter.
    references = [
        ("CC1=CN=C(C(=C1OC)C)CS(=O)C2=NC3=C(N2)C=C(C=C3)OC", 0.9556329),
        ("CN1CC[C@]23c4c5ccc(O)c4O[C@H]2[C@@H](O)C=C[C@H]3[C@H]1C5", 0.0028359715),
        ("CC1=C(C=C(C=C1)NC(=O)C2=CC=C(C=C2)CN3CCN(CC3)C)NC4=NC=CC(=N4)C5=CN=CC=C5.CS(=O)(=O)O", 0.99259007),
    ]
    checks = []
    for index, (smiles, expected) in enumerate(references):
        actual = float(restored.predict(xgb.DMatrix(fingerprint(smiles)))[0])
        if index < 2 and abs(actual - expected) > 1e-6:
            raise RuntimeError("RAscore published reference check failed.")
        original = float(booster.predict(xgb.DMatrix(fingerprint(smiles)))[0])
        if abs(actual - original) > 1e-7:
            raise RuntimeError("Converted RAscore model differs from the source booster.")
        checks.append({"smiles": smiles, "published": expected, "current_runtime": actual,
                       "matches_published_1e_6": abs(actual - expected) <= 1e-6})
    temporary.replace(MODEL)
    manifest = {"repository": REPOSITORY, "commit": COMMIT, "source_sha256": SHA256,
                "model": "XGB_chembl_ecfp_counts", "xgboost": xgb.__version__,
                "converted_sha256": hashlib.sha256(MODEL.read_bytes()).hexdigest(),
                "reference_checks": checks, "conversion_checks": "3 source-booster predictions preserved within 1e-7",
                "license": "Upstream repository MIT; see docs/ACCESSIBILITY_SCORES.md"}
    MODEL.with_suffix(".provenance.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("RAscore ready: conversion verified; see provenance for published-example comparisons.")


if __name__ == "__main__":
    main()
