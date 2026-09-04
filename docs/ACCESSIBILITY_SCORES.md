# Accessibility scores

The preview computes both scores locally and caches identical canonical SMILES.
These are model/heuristic estimates, not measured properties or synthesis yields.
Neither guarantees that the current search will solve a molecule.

| Score | Implementation | Interpretation |
|---|---|---|
| SAScore | RDKit 2023.09.6 Contrib `SA_Score.sascorer.calculateScore`, including its bundled fragment scores | 1–10; lower is easier by fragment frequency and structural complexity |
| RAScore | RAscore `XGB_chembl_ecfp_counts`, XGBoost 2.1.4 | 0–1; classifier output for accessibility according to the original AiZynthFinder training labels; higher is more accessible |

Sources: [RDKit SA_Score](https://github.com/rdkit/rdkit/tree/Release_2023_09_6/Contrib/SA_Score),
[RAscore source](https://github.com/reymond-group/RAscore/tree/cb77db503ee5cbf0e8bb8963df6e5b76b3a94f06),
[Thakkar et al., Chemical Science 2021](https://doi.org/10.1039/D0SC05401A).

## Source and installation

`python -m explorer.setup_accessibility` clones the official repository to
`external/RAscore` and checks out commit `cb77db503ee5cbf0e8bb8963df6e5b76b3a94f06`.
An existing checkout is preserved. The model must match SHA-256
`7ca8461207e76ded1224f393e7bdb21973b5c6caece2a4e550e6396efe2cf9f7` before loading.
The clone is intentionally separate and ignored by the parent Git repository;
it is not an accidentally embedded repository or a submodule. Git is required.
No training data, clone, or model weights are committed to Explorer.

The RA fingerprint follows the source implementation, rather than the conflicting
README description: Morgan radius 3, counts, `useFeatures=False`, folded to 2048.
The DNN model is not used. Salts and disconnected fragments are retained as entered;
no salt stripping or chemical standardization beyond RDKit parsing/canonicalization
is applied. Applicability is strongest for chemistry resembling the ChEMBL training set.

The legacy Python classifier wrapper is incompatible with current packages.
Setup restores only a checksum-verified upstream pickle, maps its obsolete unused
label-encoder metadata, and exports the native booster to XGBoost JSON. Runtime
inference uses the native booster without the classifier wrapper or TensorFlow.
Python reads model bytes before passing them to XGBoost, supporting Unicode paths.
This is a tested compatibility adapter, not an upstream-supported upgrade.
[XGBoost documents that old pickle compatibility is not guaranteed](https://xgboost.readthedocs.io/en/stable/tutorials/saving_model.html).

`data/rascore-xgb.provenance.json` records the source/converted hashes, model,
runtime version and example comparisons. Setup verifies that conversion preserves
three source-booster predictions within 1e-7. The app never accepts user-uploaded pickles.
Download/clone failures stop setup; rerun setup after resolving the error.

## Verification and limits

Windows x64, Python 3.11, RDKit 2023.09.6 and XGBoost 2.1.4 were exercised.
macOS Apple Silicon and Intel have not been tested on native machines.
PyPI supplies Intel and Apple Silicon wheels for XGBoost 2.1.4; the Apple Silicon
wheel requires macOS 12 or newer. The macOS setup installs Conda llvm-openmp
for the XGBoost OpenMP runtime. This dependency step is not yet natively verified.

| Upstream README example | README XGB score | Current runtime |
|---|---:|---:|
| Omeprazole | 0.9556329 | 0.955632925 |
| Morphine | 0.0028359715 | 0.002835972 |
| Imatinib mesylate | 0.99259007 | 0.986637235 |

Two examples agree within 1e-6. The imatinib mesylate discrepancy is unresolved;
do not treat this runtime as an exact reproduction of the original published
environment. Conversion preserves the current source-booster output for all three.
Aspirin gives SAScore 1.580039750 and RAScore 0.994169950 in this environment.
The scores should support exploratory comparison, not experimental decisions.

## Licenses

The RAscore repository supplies an MIT license, Copyright (c) 2020 Reymond Research
Group, University of Bern. Its model is obtained from that pinned repository;
no separate model-specific license was found there. Preserve the repository notice
and attribution. This does not establish blanket rights to redistribute its
underlying ChEMBL training data, which Explorer does not download or redistribute.
SA_Score's Novartis BSD notice and the RAscore MIT text are in `docs/licenses/`.
Downloading separately does not remove notice obligations.
