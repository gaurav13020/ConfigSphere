# Realtime Config Fetch Demo

## Purpose

- Run a separate demo stack with real dummy services polling delivery
- Expose each dummy service group's current config and last update time
- Render a dedicated dashboard outside the main control-plane UI

## Components

- `demo-service`
  - Python FastAPI container
  - simulates one service group with multiple instances
  - polls delivery every few seconds using a delivery API token
  - exposes `/config` with the latest in-memory state of every instance
- `demo-dashboard`
  - Python FastAPI container
  - polls all dummy services
  - renders a live HTML dashboard at `/`

## Compose

- File: `docker-compose.demo.yml`
- Dashboard port: `8300`
- Default fleet:
  - 10 dummy service groups
  - 11 instances per group
  - 110 total simulated instances

## Setup

1. Start the main V2 stack so delivery is reachable on `http://localhost:8101`
2. In the main Services page, create delivery tokens for the services you want to demonstrate
3. Export those tokens as env vars before starting the demo stack:

```bash
export DEMO_CONFIG_TOKEN_01=cfgsdk_...
export DEMO_CONFIG_TOKEN_02=cfgsdk_...
export DEMO_CONFIG_TOKEN_03=cfgsdk_...
export DEMO_CONFIG_TOKEN_04=cfgsdk_...
export DEMO_CONFIG_TOKEN_05=cfgsdk_...
export DEMO_CONFIG_TOKEN_06=cfgsdk_...
export DEMO_CONFIG_TOKEN_07=cfgsdk_...
export DEMO_CONFIG_TOKEN_08=cfgsdk_...
export DEMO_CONFIG_TOKEN_09=cfgsdk_...
export DEMO_CONFIG_TOKEN_10=cfgsdk_...
docker compose -f docker-compose.demo.yml up --build
```

## Notes

- The default demo compose points all groups at delivery service `payments` and path `/global/us-east-1`
- Adjust `DELIVERY_SERVICE_NAME` and `CONFIG_PATH` per demo service in `docker-compose.demo.yml` if your live dataset differs
- The dashboard is read-only and intended purely for rollout demonstrations
