from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from medallion_flow.erd import build_erd_dot
from medallion_flow.repository import load_architecture


DATA_PATH = Path("data/sample_architecture.yaml")


st.set_page_config(
    page_title="Medallion ERD",
    layout="wide",
)


@st.cache_data
def get_architecture(path: str):
    return load_architecture(Path(path))


def main() -> None:
    architecture = get_architecture(str(DATA_PATH))
    erd_lookup = architecture.erd_by_dataset_id()

    st.title("Silver Layer ERD")
    st.link_button("Back to flow map", "/")

    if not erd_lookup:
        st.info("No ERDs are defined in the architecture YAML yet.")
        return

    query_dataset_id = st.query_params.get("dataset_id")
    dataset_ids = sorted(erd_lookup)
    default_index = dataset_ids.index(query_dataset_id) if query_dataset_id in dataset_ids else 0

    selected_dataset_id = st.selectbox(
        "Dataset",
        options=dataset_ids,
        index=default_index,
        format_func=lambda dataset_id: erd_lookup[dataset_id].name,
    )
    if selected_dataset_id != query_dataset_id:
        st.query_params["dataset_id"] = selected_dataset_id

    erd = erd_lookup[selected_dataset_id]
    node = architecture.node_by_id().get(selected_dataset_id)

    if node:
        cols = st.columns([1, 1, 2])
        cols[0].metric("Layer", node.layer.value.title())
        cols[1].metric("Owner", node.owner)
        cols[2].write(node.description)

    if erd.description:
        st.caption(erd.description)

    diagram_tab, tables_tab, relationships_tab = st.tabs(
        ["Diagram", "Tables", "Relationships"]
    )
    with diagram_tab:
        st.graphviz_chart(build_erd_dot(erd), width='stretch')

    with tables_tab:
        st.dataframe(table_frame(erd), width='stretch', hide_index=True)

    with relationships_tab:
        st.dataframe(relationship_frame(erd), width='stretch', hide_index=True)


def table_frame(erd) -> pd.DataFrame:
    rows = []
    for table in erd.tables:
        for column in table.columns:
            rows.append(
                {
                    "Table": table.name,
                    "Column": column.name,
                    "Type": column.type,
                    "Primary Key": column.primary_key,
                    "Foreign Key": column.foreign_key,
                    "Nullable": column.nullable,
                }
            )
    return pd.DataFrame(rows)


def relationship_frame(erd) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "From Table": relationship.source_table,
                "From Column": relationship.source_column,
                "To Table": relationship.target_table,
                "To Column": relationship.target_column,
                "Cardinality": relationship.cardinality,
                "Description": relationship.description,
            }
            for relationship in erd.relationships
        ]
    )


if __name__ == "__main__":
    main()
