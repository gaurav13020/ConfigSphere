# Local Development

## Start the stack

```bash
cd ConfigSphere/v2
cp .env.example .env
docker compose up --build
```

To start the UI too:

```bash
docker compose --profile ui up --build
```

## Services

- Control Plane: `http://localhost:8100`
- Delivery: `http://localhost:8101`
- Frontend: `http://localhost:3001` when using the `ui` profile
- Keycloak: `http://localhost:8080`
- PostgreSQL: `localhost:5433`
- DynamoDB Local: `http://localhost:8002`

## Notes

- `AUTH_DEV_MODE=true` allows a development fallback for authenticated requests.
- PostgreSQL schema is created by Alembic in the control-plane container.
- DynamoDB Local table bootstrapping is done by the application on startup if missing.
- On lower-memory machines, keep the frontend under the `ui` profile so it is only started when needed.
