from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from medallion_flow.models import (
    Architecture,
    DatasetErd,
    DatasetNode,
    ErdTable,
    Layer,
    LineageEdge,
    TableColumn,
    TableRelationship,
)


def load_architecture(path: Path) -> Architecture:
    with path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}

    nodes = tuple(_parse_node(item) for item in raw.get("nodes", []))
    edges = tuple(_parse_edge(item) for item in raw.get("edges", []))
    erds = tuple(_parse_erd(item) for item in raw.get("erds", []))
    _validate_references(nodes, edges, erds)

    return Architecture(nodes=nodes, edges=edges, erds=erds)


def _parse_node(item: dict[str, Any]) -> DatasetNode:
    return DatasetNode(
        id=str(item["id"]),
        name=str(item["name"]),
        layer=Layer(str(item["layer"]).lower()),
        system=str(item.get("system", "")),
        owner=str(item.get("owner", "")),
        description=str(item.get("description", "")),
        freshness=str(item.get("freshness", "")),
        quality_status=str(item.get("quality_status", "unknown")),
        row_count=item.get("row_count"),
        tags=tuple(str(tag) for tag in item.get("tags", [])),
    )


def _parse_edge(item: dict[str, Any]) -> LineageEdge:
    return LineageEdge(
        source=str(item["source"]),
        target=str(item["target"]),
        transformation=str(item.get("transformation", "")),
        schedule=str(item.get("schedule", "")),
    )


def _parse_erd(item: dict[str, Any]) -> DatasetErd:
    return DatasetErd(
        dataset_id=str(item["dataset_id"]),
        name=str(item.get("name", item["dataset_id"])),
        description=str(item.get("description", "")),
        tables=tuple(_parse_erd_table(table) for table in item.get("tables", [])),
        relationships=tuple(
            _parse_table_relationship(relationship)
            for relationship in item.get("relationships", [])
        ),
    )


def _parse_erd_table(item: dict[str, Any]) -> ErdTable:
    return ErdTable(
        name=str(item["name"]),
        description=str(item.get("description", "")),
        columns=tuple(_parse_table_column(column) for column in item.get("columns", [])),
    )


def _parse_table_column(item: dict[str, Any]) -> TableColumn:
    return TableColumn(
        name=str(item["name"]),
        type=str(item.get("type", "")),
        nullable=bool(item.get("nullable", True)),
        primary_key=bool(item.get("primary_key", False)),
        foreign_key=str(item.get("foreign_key", "")),
    )


def _parse_table_relationship(item: dict[str, Any]) -> TableRelationship:
    return TableRelationship(
        source_table=str(item["source_table"]),
        source_column=str(item["source_column"]),
        target_table=str(item["target_table"]),
        target_column=str(item["target_column"]),
        cardinality=str(item.get("cardinality", "")),
        description=str(item.get("description", "")),
    )


def _validate_references(
    nodes: tuple[DatasetNode, ...],
    edges: tuple[LineageEdge, ...],
    erds: tuple[DatasetErd, ...],
) -> None:
    node_ids = {node.id for node in nodes}
    missing = sorted(
        reference
        for edge in edges
        for reference in (edge.source, edge.target)
        if reference not in node_ids
    )
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Lineage edges reference unknown node ids: {joined}")

    missing_erd_datasets = sorted(erd.dataset_id for erd in erds if erd.dataset_id not in node_ids)
    if missing_erd_datasets:
        joined = ", ".join(missing_erd_datasets)
        raise ValueError(f"ERDs reference unknown dataset ids: {joined}")

    for erd in erds:
        table_names = {table.name for table in erd.tables}
        columns_by_table = {
            table.name: {column.name for column in table.columns}
            for table in erd.tables
        }
        missing_tables = sorted(
            table
            for relationship in erd.relationships
            for table in (relationship.source_table, relationship.target_table)
            if table not in table_names
        )
        if missing_tables:
            joined = ", ".join(missing_tables)
            raise ValueError(f"ERD for {erd.dataset_id} references unknown tables: {joined}")

        missing_columns = sorted(
            f"{table}.{column}"
            for relationship in erd.relationships
            for table, column in (
                (relationship.source_table, relationship.source_column),
                (relationship.target_table, relationship.target_column),
            )
            if table in columns_by_table and column not in columns_by_table[table]
        )
        if missing_columns:
            joined = ", ".join(missing_columns)
            raise ValueError(f"ERD for {erd.dataset_id} references unknown columns: {joined}")
