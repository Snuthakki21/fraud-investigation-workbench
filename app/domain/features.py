def _velocity(transactions):
    ordered = sorted(transactions, key=lambda tx: (tx["time"], tx["id"]))
    best, left, best_ids = 0, 0, []
    for right, tx in enumerate(ordered):
        while (tx["time"] - ordered[left]["time"]).total_seconds() > 3600:
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
            best_ids = [x["id"] for x in ordered[left:right + 1]]
    return best, best_ids

class ActivityFeatureExtractor:
    @staticmethod
    def extract(entity_ids, graph, threshold):
        outgoing, incoming, membership, component_ids = graph.outgoing, graph.incoming, graph.membership, graph.component_ids
        features, evidence_map = [], {}
        for entity in sorted(entity_ids):
            inbound, outbound = incoming[entity], outgoing[entity]
            incoming_total = sum(tx["cents"] for tx in inbound)
            outgoing_total = sum(tx["cents"] for tx in outbound)
            fan_in = len({tx["from"] for tx in inbound})
            fan_out = len({tx["to"] for tx in outbound})
            velocity, velocity_ids = _velocity(outbound)
            eligible_outbound = []
            if inbound:
                first_receipt = min(tx["time"] for tx in inbound)
                eligible_outbound = [tx for tx in outbound if 0 <= (tx["time"] - first_receipt).total_seconds() <= 86400]
            pass_through = sum(tx["cents"] for tx in eligible_outbound) / incoming_total if incoming_total else None
            recent_pass_through = bool(eligible_outbound)
            indicators = []
            if velocity >= 4:
                indicators.append({"id": f"{entity}:velocity", "points": 30, "observation": f"{velocity} outgoing transfers in a rolling 60-minute window.", "transaction_ids": velocity_ids})
            if fan_in >= 3 and fan_out >= 1 and pass_through is not None and .8 <= pass_through <= 1.2 and recent_pass_through:
                indicators.append({"id": f"{entity}:pass-through", "points": 45, "observation": f"{fan_in} distinct senders with {pass_through:.1%} of inbound value sent onward within a one-day observation span; possible pass-through activity requires review.", "transaction_ids": [tx["id"] for tx in inbound + outbound]})
            if membership[entity]:
                indicators.append({"id": f"{entity}:cycle", "points": 40, "observation": f"Participates in {len(membership[entity])} directed three-account cycle(s). Cycles can also reflect legitimate treasury activity.", "cycle_ids": membership[entity]})
            for indicator in indicators:
                evidence_map[indicator["id"]] = indicator["observation"]
            score = min(100, sum(x["points"] for x in indicators))
            features.append({"entity_id": entity, "priority_score": score, "review_required": score >= threshold, "inbound_amount": incoming_total / 100, "outbound_amount": outgoing_total / 100, "distinct_senders": fan_in, "distinct_recipients": fan_out, "max_outgoing_per_hour": velocity, "pass_through_ratio": round(pass_through, 4) if pass_through is not None else None, "component_id": component_ids[entity], "indicators": indicators})
        features.sort(key=lambda row: (-row["priority_score"], row["entity_id"]))
        return features, evidence_map
