from __future__ import annotations

from urllib.parse import quote

from medallion_flow.models import Architecture, LAYER_ORDER, Layer


LAYER_COLORS: dict[Layer, str] = {
    Layer.SOURCE: "#e2e8f0",
    Layer.BRONZE: "#d6b184",
    Layer.SILVER: "#cbd5e1",
    Layer.GOLD: "#fde68a",
    Layer.SEMANTIC: "#bfdbfe",
}


def build_dot(
    architecture: Architecture,
    selected_layers: set[Layer],
    erd_node_ids: set[str] | None = None,
) -> str:
    erd_node_ids = erd_node_ids or set()
    visible_nodes = [node for node in architecture.nodes if node.layer in selected_layers]
    visible_ids = {node.id for node in visible_nodes}
    visible_edges = [
        edge
        for edge in architecture.edges
        if edge.source in visible_ids and edge.target in visible_ids
    ]

    lines = [
        "digraph medallion {",
        "  graph [rankdir=LR, bgcolor=transparent, pad=0.2, nodesep=0.6, ranksep=0.9];",
        "  node [shape=box, style=\"rounded,filled\", color=\"#94a3b8\", fontname=\"Helvetica\", fontsize=11, margin=\"0.12,0.08\"];",
        "  edge [color=\"#64748b\", arrowsize=0.7, fontname=\"Helvetica\", fontsize=9];",
    ]

    for layer in LAYER_ORDER:
        layer_nodes = [node for node in visible_nodes if node.layer == layer]
        if not layer_nodes:
            continue

        lines.append(f"  subgraph cluster_{layer.value} {{")
        lines.append(f"    label=\"{layer.value.title()}\";")
        lines.append("    color=\"#cbd5e1\";")
        lines.append("    style=\"rounded\";")
        for node in layer_nodes:
            label = f"{node.name}\\n{node.system}"
            color = LAYER_COLORS[node.layer]
            link_attributes = ""
            if node.id in erd_node_ids:
                href = f"/ERD?dataset_id={quote(node.id)}"
                link_attributes = (
                    f", URL=\"{href}\", target=\"_self\", tooltip=\"Open ERD for {node.name}\""
                )
            lines.append(
                f"    \"{_dot_escape(node.id)}\" "
                f"[label=\"{_dot_escape(label)}\", fillcolor=\"{color}\"{link_attributes}];"
            )
        lines.append("  }")

    for edge in visible_edges:
        label = edge.transformation or edge.schedule
        label_part = f" [label=\"{_dot_escape(label)}\"]" if label else ""
        lines.append(
            f"  \"{_dot_escape(edge.source)}\" -> \"{_dot_escape(edge.target)}\"{label_part};"
        )

    lines.append("}")
    return "\n".join(lines)


def _dot_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
