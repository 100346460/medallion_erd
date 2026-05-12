from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Layer(str, Enum):
    SOURCE = "source"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    SEMANTIC = "semantic"


LAYER_ORDER: tuple[Layer, ...] = (
    Layer.SOURCE,
    Layer.BRONZE,
    Layer.SILVER,
    Layer.GOLD,
    Layer.SEMANTIC,
)


@dataclass(frozen=True)
class DatasetNode:
    id: str
    name: str
    layer: Layer
    system: str
    owner: str
    description: str = ""
    freshness: str = ""
    quality_status: str = "unknown"
    row_count: int | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class LineageEdge:
    source: str
    target: str
    transformation: str = ""
    schedule: str = ""


@dataclass(frozen=True)
class TableColumn:
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: str = ""


@dataclass(frozen=True)
class ErdTable:
    name: str
    description: str = ""
    columns: tuple[TableColumn, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TableRelationship:
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    cardinality: str = ""
    description: str = ""


@dataclass(frozen=True)
class DatasetErd:
    dataset_id: str
    name: str
    description: str = ""
    tables: tuple[ErdTable, ...] = field(default_factory=tuple)
    relationships: tuple[TableRelationship, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Architecture:
    nodes: tuple[DatasetNode, ...]
    edges: tuple[LineageEdge, ...]
    erds: tuple[DatasetErd, ...] = field(default_factory=tuple)

    def node_by_id(self) -> dict[str, DatasetNode]:
        return {node.id: node for node in self.nodes}

    def erd_by_dataset_id(self) -> dict[str, DatasetErd]:
        return {erd.dataset_id: erd for erd in self.erds}

    def nodes_for_layer(self, layer: Layer) -> tuple[DatasetNode, ...]:
        return tuple(node for node in self.nodes if node.layer == layer)

    def downstream_edges(self, node_id: str) -> tuple[LineageEdge, ...]:
        return tuple(edge for edge in self.edges if edge.source == node_id)

    def upstream_edges(self, node_id: str) -> tuple[LineageEdge, ...]:
        return tuple(edge for edge in self.edges if edge.target == node_id)
