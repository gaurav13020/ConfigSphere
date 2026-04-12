# Jira Sync

This slice persists Jira sync intent in `jira_sync_events` and emits the required state changes through the worker pipeline.

Current implementation level:

- create Jira sync event records
- keep internal request state authoritative
- leave full Jira REST integration as the next implementation increment

Planned events:

- request created
- request submitted
- review changes requested
- approved
- implementing
- implemented
- failed
- conflicted
- rollback requested
- rollback completed
