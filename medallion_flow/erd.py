from __future__ import annotations

from medallion_flow.models import DatasetErd, TableColumn


def build_erd_dot(erd: DatasetErd) -> str:
    lines = [
        "digraph erd {",
        "  graph [rankdir=LR, bgcolor=transparent, pad=0.2, nodesep=0.7, ranksep=1.0];",
        "  node [shape=plaintext, fontname=\"Helvetica\"];",
        "  edge [color=\"#475569\", arrowsize=0.7, fontname=\"Helvetica\", fontsize=9];",
    ]

    for table in erd.tables:
        rows = "\n".join(_column_row(column) for column in table.columns)
        label = f"""<
<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="6" COLOR="#94a3b8">
  <TR><TD BGCOLOR="#e0f2fe"><B>{_html_escape(table.name)}</B></TD></TR>
  {rows}
</TABLE>
>"""
        lines.append(f"  \"{_dot_escape(table.name)}\" [label={label}];")

    for relationship in erd.relationships:
        label = relationship.cardinality or (
            f"{relationship.source_column} -> {relationship.target_column}"
        )
        tooltip = relationship.description or label
        lines.append(
            "  "
            f"\"{_dot_escape(relationship.source_table)}\" -> "
            f"\"{_dot_escape(relationship.target_table)}\" "
            f"[label=\"{_dot_escape(label)}\", tooltip=\"{_dot_escape(tooltip)}\"];"
        )

    lines.append("}")
    return "\n".join(lines)


def _column_row(column: TableColumn) -> str:
    key_prefix = ""
    if column.primary_key:
        key_prefix = "PK "
    elif column.foreign_key:
        key_prefix = "FK "

    nullable = "" if column.nullable else " not null"
    label = f"{key_prefix}{column.name}: {column.type}{nullable}"
    return f'  <TR><TD ALIGN="LEFT">{_html_escape(label)}</TD></TR>'


def _dot_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _html_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
