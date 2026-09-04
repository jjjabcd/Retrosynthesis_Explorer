# Model and data sources

Metadata checked on 2026-09-04 against the official APIs. The exact asset sizes
and publisher MD5 checksums are pinned in [`explorer/assets.json`](../explorer/assets.json).
The downloader also records local SHA-256 hashes and retrieval time in
`data/manifest.json`, which is copied into search result exports.

| Component | Pinned source | Attribution | Record license |
|---|---|---|---|
| USPTO expansion/filter ONNX models | [Zenodo 7797465, v1](https://doi.org/10.5281/zenodo.7797465), 2023-04-04 | Lakshidaa Saigiridharan, *USPTO-based ONNX models* | CC BY 4.0 |
| USPTO unique reaction templates | [Zenodo 7341155, v1](https://doi.org/10.5281/zenodo.7341155), 2022-11-22 | Samuel Genheden, *PaRoutes 2.0 and USPTO-based models* | CC BY 4.0 |
| ZINC stock | [Figshare 12334577, v1](https://doi.org/10.6084/m9.figshare.12334577.v1), file ID 23086469 | Samuel Genheden, Veronika Chadimova, Ola Engkvist (v1 API author list), *AiZynthFinder: a fast, robust and flexible open-source software for retrosynthetic planning* | MIT |

The stock is the ZINC snapshot dated 2020-04-17, not current supplier inventory.
Its original filename is `zinc_stock_17_04_20.hdf5`; it is stored locally as
`zinc_stock.hdf5`. The templates are renamed from
`uspto_unique_templates.csv.gz` to `uspto_templates.csv.gz`.
Downloaded file bytes are not modified.

The default download is approximately 775 MB (decimal). The upstream downloader
also lists RingBreaker ONNX weights and templates in the same Zenodo records.
Their exact files are recorded in the asset catalog and can be downloaded with
`python -m explorer.download --include-ringbreaker`; this GUI currently selects
the USPTO policy only. No replacement files from unofficial mirrors are used.

## Terms and retained notices

For CC BY 4.0 materials, retain the creator attribution, source link, license
link and any supplied notices, and identify modifications. Do not imply
endorsement or impose additional restrictions inconsistent with the license.
See the [CC BY 4.0 deed](https://creativecommons.org/licenses/by/4.0/) and
[legal code](https://creativecommons.org/licenses/by/4.0/legalcode).

The Figshare v1 metadata explicitly labels the deposited stock MIT. Retain the
MIT permission and copyright notices supplied with redistributed material;
the original AiZynthFinder MIT notice is retained in
[`aizynfinder/LICENSE`](../aizynfinder/LICENSE). The record does not provide a
separate stock-specific copyright text beyond its authorship and license field;
this document does not invent one. Retain the record attribution and metadata
when passing on the stock, and check the actual artifact for additional notices.

These statements identify the depositors' published terms for these exact
artifacts. They are not a determination that every underlying patent reaction,
supplier record, database right or other third-party right is cleared for every
possible downstream use. New datasets, modified weights and redistributed
bundles require their own review. Moving downloads outside Git does not waive
license obligations.

Official machine-readable evidence:

- [ONNX metadata](https://zenodo.org/api/records/7797465)
- [Template metadata](https://zenodo.org/api/records/7341155)
- [Stock v1 metadata](https://api.figshare.com/v2/articles/12334577/versions/1)

Search outputs record which stock and model files were used. `Solved` only means
that all terminal nodes satisfy the selected stock; it does not establish
availability today, experimental feasibility, yield or safety.

## Preview accessibility models

See [ACCESSIBILITY_SCORES.md](ACCESSIBILITY_SCORES.md) for the separately cloned
RAscore ChEMBL model, pinned source/hash, license notice, conversion, and validation
limitations, and the RDKit-bundled SA fragment scores.
