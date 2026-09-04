# Verification record

Tested on 2026-09-04 in the actual project path:
`C:\Users\rlawl\Desktop\한림대\Side Project\retrosynthesis_explorer`.
The path contains Korean characters and spaces. It is also the permitted write
root. No `AGENTS.md` was present in the inspected project/ancestor locations.

## Platform matrix

| Platform | Status |
|---|---|
| Windows x64 | Conda environment creation, setup helper, launcher, live model search, API tests and browser flow passed in this development machine. Windows build reported by Python: 10.0.26200. Not a test on every Windows release or a separate clean machine. |
| macOS Apple Silicon | Native execution not tested. Setup/run scripts implemented; Python 3.11 wheels for pinned RDKit and ONNX Runtime confirmed. |
| macOS Intel | Native execution not tested. Python 3.11 wheels confirmed for pinned ONNX Runtime 1.23.2; 1.29.0 did not list an Intel Mac wheel. |

The pinned ONNX Runtime Mac wheels require macOS 13+. Availability of these two
core wheels does not validate the entire dependency graph or installation.
The shell scripts passed Bash syntax parsing on Windows Git Bash; this is not
a macOS installation test. The `.bat` files are thin wrappers; the underlying
PowerShell setup/run paths were executed. Double-click behavior has not been
separately tested in Windows Explorer or macOS Finder.

## Environment

- Python 3.11.16, conda-forge, Windows AMD64.
- AiZynthFinder 4.4.1, preserved local source based on fork commit `8998736`.
- RDKit distribution 2023.9.6 (runtime version string 2023.09.6).
- ONNX Runtime 1.23.2, NumPy 1.26.4, reaction-utils 1.9.3.
- FastAPI 0.141.1, Uvicorn 0.52.4, Pillow 12.3.0.
- `pip check`: no broken requirements.

[`windows-python311-freeze.txt`](windows-python311-freeze.txt) records installed
third-party versions; the local AiZynthFinder wheel and editable Explorer app
are intentionally not expressed as machine-specific file URLs. This is a
Windows audit snapshot, not a portable lockfile. Install via `setup.bat` or
`setup.sh`, which use `constraints.txt` and the local sources.

The first editable Poetry install of AiZynthFinder failed when Python 3.11 read
the UTF-8 `.pth` file using CP949. The installer now builds a regular wheel from
the preserved local source. The Explorer package's setuptools editable finder
works at the actual Unicode path. Data YAML uses ASCII escapes so the preserved
upstream config reader also handles paths independently of locale.

## Checks performed

- Original files all remain present under `aizynfinder/`; the Python package name
  and upstream packaging metadata were preserved.
- Existing `origin/main` and local history were merged without rewriting either.
- Public model/template/stock sizes and publisher MD5 hashes matched. Setup was
  rerun and reused all four validated files.
- Setup diagnostics loaded expansion/filter ONNX models and ZINC stock with
  **17,422,831 entries**. RDKit molecule preview passed.
- Original notebook operation `ReactionTree.from_dict(...).to_image()` rendered
  the upstream linear route fixture through the extracted Python function.
- `python -m pytest -q`: **7 passed**. Coverage includes real Windows spawn
  lifecycle, capacity rejection, cancellation, hard timeout, worker crash,
  persistence/restart, invalid SMILES, request origin/host checks, route images,
  cache reuse, properties/JSON export and interrupted/corrupt downloads.
- Two dependency deprecation warnings arose from Starlette's HTTPX/AnyIO test
  adapter. They did not affect the passing test results.
- JavaScript syntax and Git whitespace checks passed. Bash entry points parsed.
- Repeated launcher invocation reused the running project instance; a different
  server's occupied port was rejected with instructions to select another port.
- Browser checks: English labels, real molecular preview, invalid SMILES error,
  GUI search submission and cancellation, restored completed job, route list,
  selected tree and intermediate-node descriptor table.

## Real-model smoke search

`scripts/verify_live.py` ran against the actual local server with the downloaded
public assets, not a mock engine or the synthetic test tree.

| Parameter / observation | Value |
|---|---|
| Target | Aspirin, `CC(=O)Oc1ccccc1C(=O)O` |
| Search budget | 30 seconds; 30 iterations; maximum 6 transforms |
| Total worker deadline | 300 seconds |
| Observed elapsed time | 19.5 seconds, including worker startup/model loading |
| Returned routes | 9 |
| Solved routes | 9, relative to the selected ZINC snapshot |
| Maximum observed health request latency | 0.015 seconds during this run |
| Exports | Route JSON, annotated PNG and computed properties CSV returned successfully |

These are one-machine observations, not performance guarantees. Search can
terminate at the iteration budget before the time budget. A solved route is not
experimental confirmation. The full local report remains in
`verification/live-report.json` and raw results in `results/`; both are ignored
by Git. Screenshots in `docs/images/` show the real browser interface and results.

## Not verified / not implemented

Native macOS setup and process lifecycle, a fresh Windows machine, OS-specific
double-click behavior, large-scale workloads and the complete upstream test
suite have not been verified. No claim is made about synthesis success rate,
current stock availability, laboratory conditions or experimental properties.
No public hosting, GitHub Pages, authentication, multi-user service or GPU path
is implemented.

## UI feedback update — 2026-09-04

Verified in the running browser: molecular formula atom counts use HTML subscripts;
count, dimensionless and elementary-charge unit labels are omitted from displayed
values while g/mol and Å² remain. Formula charges use superscripts. Original
numeric values and unit metadata in API/CSV exports are unchanged.

Route cards label total reaction steps and starting materials. The explanation
of state score was checked against the preserved StateScorer implementation
(95% stock coverage plus 5% depth preference). Selecting a card navigates to a
separate tree/properties page. Direct reload and Back to routes were verified
with the same stored job. The home page has no tree or properties-detail blocks.

## Accessibility scores and route controls (2026-09-04)

- Windows x64: Python 3.11.16, RDKit 2023.09.6, XGBoost 2.1.4. `pip check` passed.
- Nine tests passed, including distinct-candidate early stopping and input bounds.
- Live aspirin search with solved target 3 / return limit 2: 3 distinct solved routes
  after 4 iterations, 2 ranked routes returned. Search time 1.063 s, excluding model loading.
- Browser verified score cards, settings, separate detail navigation, Retrosynthetic route
  title, removed zoom controls and removed stock text within image nodes.
- Model conversion preserves three source-booster predictions; two published examples
  match and one differs. See ACCESSIBILITY_SCORES.md for the exact values and limitation.
- macOS native operation remains unverified.

## Layout and export chooser (2026-09-04)

- Ten tests passed: scope validation, single-node JSON, PNG rendering, valid SVG,
  molecule ZIP contents/manifest, CSV fields and route-image download headers.
- Live API checks on a saved route passed for route PNG, molecule SVG, all-molecule
  PNG ZIP, route CSV and single-node JSON.
- Browser checked the narrower stacked home layout, workspace status below routes,
  both Export entry points, molecule/format selection, and removal of the method column.
- Actual browser download verified: `route-1-M2.svg` was saved in Downloads; its
  5,073 bytes matched the selected aspirin-route M2 response and parsed as SVG.
  The automation download-event observer timed out, but the file was saved successfully.
