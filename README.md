# Medallion Flow Visualizer

A Streamlit starter app for visualizing data movement through a medallion architecture:

`source -> bronze -> silver -> gold -> semantic`

The app loads a YAML model of datasets and lineage edges, renders an interactive layer-aware flow graph, and exposes operational metadata in browsable tables.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Project Shape

```text
.
├── app.py
├── data/
│   └── sample_architecture.yaml
├── medallion_flow/
│   ├── __init__.py
│   ├── graph.py
│   ├── models.py
│   └── repository.py
├── requirements.txt
└── .streamlit/
    └── config.toml
```

## Extending It

- Add or edit nodes and edges in `data/sample_architecture.yaml`.
- Add table-level ERDs in the `erds:` section and link them to any medallion node with `dataset_id`.
- Replace the YAML loader in `medallion_flow/repository.py` with metadata from dbt, Unity Catalog, OpenLineage, a warehouse information schema, or a custom API.
- Add metric freshness, job run status, data quality checks, owners, and SLA state as new fields on `DatasetNode`.
