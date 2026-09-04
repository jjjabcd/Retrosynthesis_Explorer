# Third-party notices

## AiZynthFinder code

The source in `aizynfinder/` is the existing AiZynthFinder fork, retained at
commit `8998736` before the directory move. The import name remains
`aizynthfinder`; its own `pyproject.toml` is retained.

Copyright 2020 Samuel Genheden and Esben Bjerrum.

The complete original MIT permission notice and disclaimer are preserved in
[`aizynfinder/LICENSE`](aizynfinder/LICENSE). They apply to the vendored code,
including the original notebooks. The new app code is covered by the separate
root [`LICENSE`](LICENSE), retained from the Explorer repository's initial commit.

The notebook `aizynfinder/notebook/tree2img.ipynb` inspired `explorer/trees.py`:
`render_original()` exposes its `ReactionTree.from_dict(...).to_image()` operation;
`collect_mol_nodes()` generalizes its traversal. The annotated renderer adds
position-specific IDs. It does not perform the notebook's PubChem lookups or label
the highest score as the most likely synthesis.

## Dependencies

RDKit, reaction-utils, ONNX Runtime, FastAPI, Uvicorn, Pillow and the other Python
dependencies retain their respective licenses. They are installed by the package
manager, rather than copied into this repository. Their installed distribution
metadata and license files must accompany any future bundled distribution as
required by each license. This repository is currently distributed as source,
not as a self-contained binary installer.

## Models and data

The root MIT license does not relicense model weights, reaction templates or
stock databases. Consult [`docs/MODEL_DATA_SOURCES.md`](docs/MODEL_DATA_SOURCES.md)
for exact records, attribution, version and terms. Downloading separately does
not remove attribution or notice obligations. Model/data files and search results
are excluded from Git.

No endorsement by MolecularAI, AstraZeneca, RDKit, the data creators or dataset
hosts is implied.

## Accessibility scores

RAscore: Copyright (c) 2020 Reymond Research Group, University of Bern.
The upstream MIT notice is preserved in [docs/licenses/RAscore-MIT.txt](docs/licenses/RAscore-MIT.txt).
The fingerprint adapter follows its XGB implementation. The external clone retains its license.

RDKit Contrib SA_Score: Copyright (c) 2013, Novartis Institutes for BioMedical Research Inc.
The full BSD notice is preserved in [docs/licenses/SA_Score-BSD.txt](docs/licenses/SA_Score-BSD.txt).
XGBoost is installed separately under Apache-2.0; preserve its notices in any bundled distribution.
See [score provenance and limitations](docs/ACCESSIBILITY_SCORES.md).
