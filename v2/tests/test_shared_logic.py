from configsphere_shared.constants import MAX_DEPTH_DEFAULT, MAX_KEYS_DEFAULT, MAX_NODES_DEFAULT


def diff_keys(before: dict[str, str], after: dict[str, str]) -> list[str]:
    keys = set(before.keys()) | set(after.keys())
    return sorted([key for key in keys if before.get(key) != after.get(key)])


def derive_local_overrides(parent: dict[str, str] | None, materialized: dict[str, str]) -> dict[str, str]:
    if parent is None:
        return dict(materialized)
    return {key: value for key, value in materialized.items() if parent.get(key) != value}


def test_defaults_match_architecture_limits() -> None:
    assert MAX_NODES_DEFAULT == 100
    assert MAX_DEPTH_DEFAULT == 20
    assert MAX_KEYS_DEFAULT == 1000


def test_diff_keys_detects_added_removed_and_changed_keys() -> None:
    before = {"timeout": "1000", "currency": "USD", "legacy": "on"}
    after = {"timeout": "1500", "currency": "USD", "feature": "enabled"}
    assert diff_keys(before, after) == ["feature", "legacy", "timeout"]


def test_local_overrides_only_include_changed_values_against_parent() -> None:
    parent = {"timeout": "1000", "currency": "USD"}
    materialized = {"timeout": "1500", "currency": "USD", "feature": "on"}
    assert derive_local_overrides(parent, materialized) == {
        "timeout": "1500",
        "feature": "on",
    }
