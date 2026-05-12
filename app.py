from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from medallion_flow.graph import build_dot
from medallion_flow.models import Architecture, LAYER_ORDER, Layer
from medallion_flow.repository import load_architecture


DATA_PATH = Path("data/sample_architecture.yaml")


st.set_page_config(
    page_title="Medallion Flow Visualizer",
    layout="wide",
)


@st.cache_data
def get_architecture(path: str):
    return load_architecture(Path(path))


def main() -> None:
    architecture = get_architecture(str(DATA_PATH))

    st.title("Medallion Flow Visualizer")

    with st.sidebar:
        st.header("Filters")
        selected_layer_names = st.multiselect(
            "Layers",
            options=[layer.value for layer in LAYER_ORDER],
            default=[layer.value for layer in LAYER_ORDER],
        )
        selected_layers = {Layer(name) for name in selected_layer_names}

        owners = sorted({node.owner for node in architecture.nodes if node.owner})
        selected_owners = st.multiselect("Owners", options=owners, default=owners)

        quality_states = sorted({node.quality_status for node in architecture.nodes})
        selected_quality_states = st.multiselect(
            "Quality status",
            options=quality_states,
            default=quality_states,
        )

    filtered_nodes = [
        node
        for node in architecture.nodes
        if node.layer in selected_layers
        and (not selected_owners or node.owner in selected_owners)
        and node.quality_status in selected_quality_states
    ]
    filtered_ids = {node.id for node in filtered_nodes}
    filtered_architecture = Architecture(
        nodes=tuple(filtered_nodes),
        edges=tuple(
            edge
            for edge in architecture.edges
            if edge.source in filtered_ids and edge.target in filtered_ids
        ),
        erds=architecture.erds,
    )

    render_scorecards(filtered_architecture)

    graph_tab, datasets_tab, lineage_tab = st.tabs(["Flow Map", "Datasets", "Lineage"])
    with graph_tab:
        erd_node_ids = set(filtered_architecture.erd_by_dataset_id())
        st.graphviz_chart(
            build_dot(filtered_architecture, selected_layers, erd_node_ids),
            width='stretch',
        )
        render_silver_erd_links(filtered_architecture)
        render_node_inspector(filtered_architecture)

    with datasets_tab:
        st.dataframe(dataset_frame(filtered_architecture), width='stretch', hide_index=True)

    with lineage_tab:
        st.dataframe(edge_frame(filtered_architecture), width='stretch', hide_index=True)


def render_scorecards(architecture) -> None:
    cols = st.columns(len(LAYER_ORDER))
    for col, layer in zip(cols, LAYER_ORDER):
        count = len(architecture.nodes_for_layer(layer))
        col.metric(layer.value.title(), count)


def render_silver_erd_links(architecture: Architecture) -> None:
    erd_lookup = architecture.erd_by_dataset_id()
    silver_nodes = [
        node
        for node in architecture.nodes_for_layer(Layer.SILVER)
        if node.id in erd_lookup
    ]
    if not silver_nodes:
        return

    st.subheader("Silver ERDs")
    cols = st.columns(min(3, len(silver_nodes)))
    for index, node in enumerate(silver_nodes):
        erd = erd_lookup[node.id]
        with cols[index % len(cols)]:
            st.link_button(
                erd.name,
                f"/ERD?dataset_id={node.id}",
                width='stretch',
            )
            st.caption(node.description)


def render_node_inspector(architecture) -> None:
    if not architecture.nodes:
        st.info("No datasets match the current filters.")
        return

    node_lookup = architecture.node_by_id()
    selected_node_id = st.selectbox(
        "Inspect dataset",
        options=[node.id for node in architecture.nodes],
        format_func=lambda node_id: node_lookup[node_id].name,
    )
    node = node_lookup[selected_node_id]

    detail_cols = st.columns([1, 1, 2])
    detail_cols[0].metric("Layer", node.layer.value.title())
    detail_cols[1].metric("Quality", node.quality_status.title())
    detail_cols[2].write(f"**Owner:** {node.owner}")
    detail_cols[2].write(f"**Freshness:** {node.freshness or 'Unknown'}")
    if node.description:
        st.caption(node.description)

    upstream = [edge.source for edge in architecture.upstream_edges(node.id)]
    downstream = [edge.target for edge in architecture.downstream_edges(node.id)]
    relation_cols = st.columns(2)
    relation_cols[0].write("**Upstream**")
    relation_cols[0].write(", ".join(node_lookup[item].name for item in upstream) or "None")
    relation_cols[1].write("**Downstream**")
    relation_cols[1].write(", ".join(node_lookup[item].name for item in downstream) or "None")


def dataset_frame(architecture) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Name": node.name,
                "Layer": node.layer.value,
                "System": node.system,
                "Owner": node.owner,
                "Quality": node.quality_status,
                "Freshness": node.freshness,
                "Rows": node.row_count,
                "Tags": ", ".join(node.tags),
            }
            for node in architecture.nodes
        ]
    )


def edge_frame(architecture) -> pd.DataFrame:
    node_lookup = architecture.node_by_id()
    return pd.DataFrame(
        [
            {
                "Source": node_lookup[edge.source].name,
                "Target": node_lookup[edge.target].name,
                "Transformation": edge.transformation,
                "Schedule": edge.schedule,
            }
            for edge in architecture.edges
        ]
    )


if __name__ == "__main__":
    main()
