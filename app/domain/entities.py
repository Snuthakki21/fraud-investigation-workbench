"""Transaction graph and immutable execution identity."""
from dataclasses import dataclass

@dataclass
class TransactionGraph:
    outgoing: dict
    incoming: dict
    edges: dict
    cycles: list
    membership: dict
    component_ids: dict
    components: list

@dataclass(frozen=True)
class ActivityRevision:
    value: str
    threshold: int
