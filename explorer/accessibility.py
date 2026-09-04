"""Local SA and RA inference; classifier scores are not laboratory probabilities."""
from functools import lru_cache
from pathlib import Path
import threading

import numpy as np
from rdkit import Chem, rdBase
from rdkit.Chem import AllChem
from rdkit.Contrib.SA_Score import sascorer

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "data" / "rascore-xgb.json"
LOCK = threading.Lock()


def fingerprint(smiles):
    # Matches RAscore_XGB.py at the pinned upstream commit: radius 3,
    # non-feature Morgan counts folded to 2048, despite the folder's ECFP name.
    fp = AllChem.GetMorganFingerprint(Chem.MolFromSmiles(smiles), 3,
                                      useCounts=True, useFeatures=False)
    array = np.zeros(2048, dtype=np.int32)
    for index, count in fp.GetNonzeroElements().items():
        array[index % 2048] += int(count)
    return array.reshape(1, -1)


@lru_cache(maxsize=1)
def model():
    import xgboost as xgb
    booster = xgb.Booster(params={"nthread": 1})
    booster.load_model(bytearray(MODEL.read_bytes()))
    return booster


@lru_cache(maxsize=4096)
def scores(smiles):
    import xgboost as xgb
    with LOCK:
        sa = float(sascorer.calculateScore(Chem.MolFromSmiles(smiles)))
        result = [{"name": "SAScore", "value": sa, "range": [1, 10],
                   "method": f"RDKit {rdBase.rdkitVersion} Contrib SA_Score",
                   "note": "1 = easier; 10 = harder. Fragment and structural-complexity heuristic."}]
        ra = {"name": "RAScore", "value": None, "range": [0, 1],
              "method": f"RAscore ChEMBL XGB · XGBoost {xgb.__version__} · RDKit {rdBase.rdkitVersion}",
              "note": "Higher = more likely to be classified as accessible by the original planner. Not a laboratory synthesis success probability."}
        try:
            ra["value"] = float(model().predict(xgb.DMatrix(fingerprint(smiles)))[0])
        except (OSError, xgb.core.XGBoostError):
            ra["error"] = "RAScore model unavailable. Run setup to prepare the model."
        result.append(ra)
        return result
