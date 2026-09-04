# Architecture and implementation plan

## Repository layout

```text
retrosynthesis_explorer/
  .git/                      Single Git repository, original history preserved
  README.md / LICENSE        Explorer documentation and new-code license
  THIRD_PARTY_NOTICES.md
  pyproject.toml             Explorer app package only
  constraints.txt            Validated core dependency versions
  setup.bat / run.bat        Windows entry points
  setup.sh / run.sh           macOS entry points
  run.command                macOS double-click wrapper
  explorer/                  Local engine, API, renderer, English UI
  scripts/                   Platform helpers
  tests/                     App lifecycle and integration tests
  docs/                      Provenance, verification, screenshots
  aizynfinder/               Preserved upstream fork (intentional spelling)
    pyproject.toml
    LICENSE
    aizynthfinder/           Unchanged Python import name
    notebook/tree2img.ipynb
  data/                      Ignored downloads, config and manifest
  results/                   Ignored job metadata and exports
  .conda-env/                Ignored project-local Conda environment
```

## Git migration

The original clean `master` pointed to `8998736` and tracked
`previous-origin/master`. A backup branch `backup/pre-explorer-layout` preserves
that commit. The existing `.git` was moved to the project root; no nested Git
repository was initialized. All original source files remain under `aizynfinder/`.

`origin/main` contained initial commit `10c11ab` with a LICENSE only. The layout
commit was followed by a merge with `--allow-unrelated-histories`, retaining both
lineages and the Explorer root license. No rebase or force push is used.
The original MIT text is separately preserved in `aizynfinder/LICENSE`.

Upstream workflows remain under `aizynfinder/.github` as historical files; they
are not activated as root workflows because their PyPI publishing/deployment
behavior is outside the local-app scope.

## Runtime

FastAPI serves static HTML/CSS/JavaScript from loopback. All API work is local;
there are no CDN assets or PubChem lookups. `launcher.py` reserves the socket
before starting Uvicorn and opens the browser only after readiness. Repeated
launches recognize the same project instance. Other port occupants cause an
actionable error. Run a single Uvicorn worker.

`JobManager` serializes submissions under a lock and admits one search at a time.
Each search runs in a fresh multiprocessing **spawn** process. The worker imports
AiZynthFinder and owns model/stock memory. A monitor enforces a separate total
deadline including imports, model loading, search and route extraction. Cancel
and timeout terminate and reap the worker. Results are atomically published;
failed, cancelled or timed-out jobs cannot expose partial results as completed.
On restart, abandoned running jobs become interrupted; finished jobs remain
available. Controlled server shutdown cancels active work.

The search budget is AiZynthFinder's iteration/time limit and is checked between
search iterations. The total deadline is the hard process limit. Cancellation
does not return partial routes. Model loading repeats for each job to give a
clear cleanup boundary; it uses more startup time than a persistent model worker.

Route summaries are returned before any tree rendering. The home page contains
target input and route summaries only. Route links open `static/route.html` with
job and route IDs in the URL; this separate page displays the tree and properties.
Its back link restores the same job on the home page. Shared `common.js` formats
formula subscripts and display units without changing the JSON/CSV data.
Selecting a route
computes its occurrence IDs and descriptors; PNG rendering is cached per job and
route. The renderer connects each product to precursor molecules and labels
nodes M1, M2, ... in traversal order. It does not attempt atom mapping or provide
experimental reaction conditions. A 200-node/30-megapixel image limit bounds
rendering memory. PNG rendering is serialized and runs in the API thread pool.

Descriptor values are cached by canonical isomeric SMILES while tree occurrences
remain distinct. No salt stripping, neutralization or tautomer standardization
is silently applied. Formula, average molecular weight, Crippen cLogP, TPSA,
donors/acceptors, rotatable bonds, rings/aromatic rings and formal charge are
computed with RDKit. Each exported value includes method, unit and RDKit version.

## Remaining scope

macOS native installation and model execution require platform verification.
pKa, solubility, melting/boiling points, live supplier inventory, authentication,
multi-user scheduling, GPU execution and GitHub Pages are not implemented.
The server is intended for one trusted user on loopback. Host/origin checks
reject cross-site browser requests; there is no Internet-facing service mode.
Results and molecular input are stored in plaintext locally and are never
automatically deleted. Remove unwanted job directories only while the server
is stopped. Restart from the same project folder to retain history.
