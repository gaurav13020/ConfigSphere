# Conflict Model

## MVP policy

- only one implementation job per service at a time
- each revision stores `base_tree_version`
- implementation compares `base_tree_version` with current service `current_tree_version`
- mismatch produces `CONFLICTED`

## Current behavior

- no auto-merge
- conflicted requests must be rebased by creating a new revision
