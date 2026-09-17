from collections import defaultdict
from app.domain.entities import TransactionGraph

def _components(entity_ids, neighbors):
    mapping, groups = {}, []
    for start in sorted(entity_ids):
        if start in mapping:
            continue
        component = []
        stack = [start]
        cid = f"component-{len(groups) + 1}"
        mapping[start] = cid
        while stack:
            node = stack.pop()
            component.append(node)
            for other in sorted(neighbors[node]):
                if other not in mapping:
                    mapping[other] = cid
                    stack.append(other)
        groups.append({"id": cid, "entities": sorted(component)})
    return mapping, groups

def _triangles(entity_ids, adjacency):
    # ponytail: directed triangles only, bounded to 200 nodes/1,000 edges;
    # add longer-cycle graph algorithms only with a demonstrated investigation need.
    cycles = set()
    for a in sorted(entity_ids):
        for b in adjacency[a]:
            for c in adjacency[b]:
                if a != c and a in adjacency[c]:
                    triple = (a, b, c)
                    cycles.add(min(triple, triple[1:] + triple[:1], triple[2:] + triple[:2]))
    return sorted(cycles)

class GraphAnalyzer:
    @staticmethod
    def build(entity_ids, transactions):
        outgoing, incoming = defaultdict(list), defaultdict(list)
        adjacency, neighbors = defaultdict(set), defaultdict(set)
        edges = {}
        for tx in transactions:
            outgoing[tx["from"]].append(tx)
            incoming[tx["to"]].append(tx)
            adjacency[tx["from"]].add(tx["to"])
            neighbors[tx["from"]].add(tx["to"])
            neighbors[tx["to"]].add(tx["from"])
            key = (tx["from"], tx["to"])
            edge = edges.setdefault(key, {"from": key[0], "to": key[1], "transaction_count": 0, "total_cents": 0})
            edge["transaction_count"] += 1
            edge["total_cents"] += tx["cents"]
        cycles = _triangles(entity_ids, adjacency)
        membership = defaultdict(list)
        for index, cycle in enumerate(cycles, 1):
            for entity in cycle:
                membership[entity].append(f"cycle-{index}")
        component_ids, components = _components(entity_ids, neighbors)
        return TransactionGraph(outgoing, incoming, edges, cycles, membership, component_ids, components)
