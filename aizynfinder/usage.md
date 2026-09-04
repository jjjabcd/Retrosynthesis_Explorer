# Usage Guide (Retrosynthesis Planning)

This document explains how to run retrosynthesis planning after completing the
"For end-users" installation described in `README.md`.

## 1. Installation (recap)

```bash
conda create "python>=3.10,<3.13" -n aizynth-env
conda activate aizynth-env
python -m pip install aizynthfinder[all]
```

## 2. Preparing the data

To run a tree search, `aizynthfinder` needs three things:

1. A stock file (a list of purchasable precursors)
2. A trained expansion policy model
3. (Optional) A trained filter policy model

You can download a public USPTO-based expansion model and a ZINC-based stock
automatically. The target folder must already exist.

```bash
mkdir -p data
download_public_data data
```

This creates the following files in `data/`, along with a `config.yml` that
can be used directly with `aizynthcli`, `aizynthapp`, or `run.py`.

- `uspto_model.onnx`, `uspto_templates.csv.gz` (expansion policy: uspto)
- `uspto_ringbreaker_model.onnx`, `uspto_ringbreaker_templates.csv.gz` (expansion policy: ringbreaker)
- `uspto_filter_model.onnx` (filter policy)
- `zinc_stock.hdf5` (stock)

The generated `data/config.yml` looks like this (paths are filled in as
absolute paths):

```yaml
expansion:
  uspto:
    - data/uspto_model.onnx
    - data/uspto_templates.csv.gz
  ringbreaker:
    - data/uspto_ringbreaker_model.onnx
    - data/uspto_ringbreaker_templates.csv.gz
filter:
  uspto: data/uspto_filter_model.onnx
stock:
  zinc: data/zinc_stock.hdf5
```

## 3. Customizing the configuration

The downloaded `config.yml` is just a starting point. You can edit it (or
write your own) to point to your own trained models, add multiple
stocks/policies, or tune the search behavior. Each section accepts either the
short-cut form above or a more detailed form with explicit settings:

```yaml
search:
  algorithm: mcts
  algorithm_config:
    C: 1.4
    default_prior: 0.5
    use_prior: True
  max_transforms: 6
  iteration_limit: 100
  time_limit: 120
  return_first: false
expansion:
  my_policy:
    type: template-based
    model: /path/to/my/expansion_model.onnx
    template: /path/to/my/templates.csv.gz
    cutoff_cumulative: 0.995
    cutoff_number: 50
filter:
  my_filter:
    type: quick-filter
    model: /path/to/my/filter_model.onnx
    filter_cutoff: 0.05
stock:
  my_stock:
    type: inchiset
    path: /path/to/my/stock.hdf5
```

Notes:

- Any key (`my_policy`, `my_filter`, `my_stock`, ...) can be used as the name
  of a policy/stock; that name is what you pass to `aizynthcli --policy`,
  `--filter`, or `--stocks`, or select in the `aizynthapp` GUI.
- You can define several expansion policies, filter policies, and stocks in
  the same `config.yml` and choose which ones to use per run.
- `search` settings are optional; unset values fall back to the defaults
  shown above (e.g. `max_transforms: 6`, `iteration_limit: 100`,
  `time_limit: 120`). Values can also be read from environment variables,
  e.g. `iteration_limit: ${ITERATION_LIMIT}`.
- Stock files can be HDF5 (`table` key, `inchi_key` column), CSV
  (`inchi_key` column), or a plain text file with one InChI key per line.

See `docs/configuration.rst` and `docs/stocks.rst` for the full list of
options.

## 4. Running retrosynthesis planning

### 4-1. Basic CLI (`aizynthcli`)

Run on a batch of molecules listed in a file:

```bash
aizynthcli --config data/config.yml --smiles smiles.txt
```

Or pass a single SMILES directly on the command line, quoted:

```bash
aizynthcli --config data/config.yml --smiles "COc1cccc(OC(=O)/C=C/c2cc(OC)c(OC)c(OC)c2)c1"
```

- When SMILES are provided as a file, results are saved to `output.json.gz`
  (readable as a pandas dataframe).
- When a single SMILES is provided on the command line, statistics are
  printed to the screen and the top-ranked routes are saved to `trees.json`.

### 4-2. `run.py` wrapper script

A thin wrapper for quickly running a single molecule:

```bash
python run.py --smiles "COc1cccc(OC(=O)/C=C/c2cc(OC)c(OC)c(OC)c2)c1" --config data/config.yml
```

- `--smiles` (required): the SMILES of the target molecule
- `--config` (optional, default `data/config.yml`): path to the stock/policy
  configuration file

Internally it just calls `aizynthcli --config <config> --smiles "<smiles>"`,
so its behavior and output are identical to the single-molecule `aizynthcli`
example above.

> Note: `aizynthfinder` does not provide a `--device` option to select
> CPU/GPU. Prediction models run through ONNX Runtime and automatically use
> whichever provider is available (CPU by default).

### 4-3. GUI (Jupyter Notebook)

The tool can also be run through a GUI inside a Jupyter notebook:

```python
from aizynthfinder.interfaces import AiZynthApp

app = AiZynthApp("data/config.yml")
```

After running the cell, enter the target SMILES in the GUI, select the
stock/policy, and press `Run Search` to perform the tree search. Press
`Show Reactions` to view the top-ranked routes.

## 5. Checking the results

- For a batch run (`output.json.gz`):

  ```python
  import pandas as pd

  data = pd.read_json("output.json.gz", orient="table")
  ```

- Each row contains statistics such as `search_time`, `is_solved`,
  `number_of_steps`, `top_score`, and `trees` (a list of route JSONs). See
  `docs/cli.rst` for the full column reference.

For more details, see the [official documentation](https://molecularai.github.io/aizynthfinder/).
