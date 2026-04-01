# ConfigSphere Python SDK

Python client for the ConfigSphere Real-Time Configuration Management System. Polls the Config Server API, maintains a thread-safe in-memory cache, and delivers configuration changes to your microservice without restarts.

## Installation

```bash
pip install configsphere
```

Or install from source:

```bash
cd sdk/python
pip install -e .
```

## Quick Start

```python
from configsphere import ConfigSphereClient, SDKConfig, ScopeParams

config = SDKConfig(
    server_url="http://localhost:8000/api/v1",
    scope=ScopeParams(service_name="payment-svc", region_name="us-west"),
    poll_interval_sec=15,
)

with ConfigSphereClient(config) as client:
    db_url = client.get("database_url", "localhost:5432")
    all_config = client.get_all()
    print(f"Database URL: {db_url}")
```

## Change Notifications

```python
def handle_change(diff):
    for key, change in diff.items():
        print(f"{key}: {change['old']} -> {change['new']}")

client = ConfigSphereClient(config)
client.on_change(handle_change)
client.start()
```

## Configuration

`SDKConfig` accepts the following parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `server_url` | (required) | Config Server API base URL |
| `scope` | (required) | `ScopeParams` identifying the config hierarchy |
| `poll_interval_sec` | `30.0` | Seconds between polls |
| `request_timeout_sec` | `10.0` | HTTP request timeout |
| `max_backoff_sec` | `300.0` | Maximum backoff delay on errors |
| `base_backoff_sec` | `1.0` | Initial backoff delay |
| `backoff_multiplier` | `2.0` | Exponential backoff multiplier |
| `backoff_jitter` | `True` | Add random jitter to backoff |
| `auth_token` | `None` | Authorization header value |

## Logging

The SDK uses Python's standard `logging` module with the logger name `configsphere`:

```python
import logging
logging.getLogger("configsphere").setLevel(logging.DEBUG)
```

## Requirements

- Python >= 3.10
- requests >= 2.28
