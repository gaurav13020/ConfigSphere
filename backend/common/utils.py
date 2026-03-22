import hashlib
import json


def compute_checksum(payload: dict) -> str:
    """
    Deterministic SHA-256 checksum over a JSON payload.
    Canonical form: sorted keys, compact separators, no whitespace.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def merge_payloads(layers: list[dict]) -> dict:
    """
    Shallow merge a list of dicts in order of increasing precedence.
    Later dicts override earlier ones.

    For v1 we use a shallow merge (top-level key wins).
    Deep/recursive merge can be added later as a strategy option.
    """
    result = {}
    for layer in layers:
        result.update(layer)
    return result
