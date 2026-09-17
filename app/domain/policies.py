from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import re

def _valid_id(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value))

def _validate(payload):
    if not isinstance(payload, dict):
        raise ValueError("Input must be an object.")
    entities = payload.get("entities")
    if not isinstance(entities, list) or not 2 <= len(entities) <= 200:
        raise ValueError("entities must contain 2–200 synthetic accounts.")
    entity_ids = set()
    for entity in entities:
        if not isinstance(entity, dict) or set(entity) != {"id", "kind"} or not _valid_id(entity.get("id")) or not isinstance(entity.get("kind"), str) or entity["kind"] not in {"account", "merchant", "treasury"}:
            raise ValueError("Each entity must contain only id and kind (account, merchant or treasury). No personal traits are accepted.")
        if entity["id"] in entity_ids:
            raise ValueError("Entity ids must be unique.")
        entity_ids.add(entity["id"])
    raw_transactions = payload.get("transactions")
    if not isinstance(raw_transactions, list) or not 1 <= len(raw_transactions) <= 1000:
        raise ValueError("transactions must contain 1–1,000 records.")
    transaction_ids, transactions = set(), []
    for tx in raw_transactions:
        if not isinstance(tx, dict) or set(tx) != {"id", "from", "to", "amount", "timestamp"}:
            raise ValueError("Transactions require exactly id, from, to, amount and timestamp.")
        if not _valid_id(tx["id"]) or tx["id"] in transaction_ids:
            raise ValueError("Transaction ids must be valid and unique.")
        if not isinstance(tx["from"], str) or not isinstance(tx["to"], str) or tx["from"] not in entity_ids or tx["to"] not in entity_ids or tx["from"] == tx["to"]:
            raise ValueError("Transaction endpoints must reference distinct known entities.")
        amount = tx["amount"]
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not 0 < amount <= 10000000 or not math.isfinite(amount):
            raise ValueError("Transaction amounts must be finite positive numbers no greater than 10 million.")
        try:
            value = Decimal(str(amount))
            if value <= 0 or value > 10000000 or value != value.quantize(Decimal("0.01")):
                raise ValueError()
            cents = int(value * 100)
        except (InvalidOperation, ValueError):
            raise ValueError("Amounts must be positive, at most 10 million, and have at most two decimal places.") from None
        try:
            stamp = datetime.fromisoformat(tx["timestamp"].replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError()
            stamp = stamp.astimezone(timezone.utc)
        except (AttributeError, TypeError, ValueError, OverflowError):
            raise ValueError("Transaction timestamp must be an ISO datetime with a UTC offset.") from None
        transaction_ids.add(tx["id"])
        transactions.append({**tx, "cents": cents, "time": stamp})
    threshold = payload.get("review_threshold", 60)
    if type(threshold) is not int or not 1 <= threshold <= 100:
        raise ValueError("review_threshold must be an integer from 1 to 100.")
    reviews = payload.get("case_reviews", [])
    if not isinstance(reviews, list) or len(reviews) > 300:
        raise ValueError("case_reviews must contain at most 300 human review events.")
    labels = payload.get("ground_truth")
    if labels is not None and (not isinstance(labels, dict) or set(labels) != entity_ids or any(type(x) is not bool for x in labels.values())):
        raise ValueError("ground_truth must label every entity with a boolean, or be omitted.")
    return entity_ids, transactions, threshold, reviews, labels
