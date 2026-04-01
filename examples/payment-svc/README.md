# payment-svc — ConfigSphere Python SDK Demo

A minimal Flask microservice that embeds the ConfigSphere Python SDK and displays real-time configuration changes in a browser dashboard.

## What It Shows

- **Live config polling**: The SDK polls the ConfigSphere backend every 5 seconds
- **Auto-refreshing dashboard**: Browser updates every 3 seconds without a page reload
- **Change history**: Every config diff is captured and displayed with a timestamp
- **Row highlighting**: Changed config values flash yellow when they update

## Prerequisites

The ConfigSphere backend stack must be running:
```bash
cd ../../backend && docker compose up
```

## Setup

From this directory (`examples/payment-svc/`):

```bash
# Install the ConfigSphere SDK (editable, from source)
pip install -e ../../sdk/python

# Install Flask
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Open [http://localhost:5050](http://localhost:5050) in your browser.

## Demo: Watching a Config Change

1. Open [http://localhost:5050](http://localhost:5050) — you'll see the current `payment_config` values
2. Open [http://localhost:3000](http://localhost:3000) — ConfigSphere admin dashboard
3. Navigate to **Config Items** → `payment_config` (global scope)
4. Create a new version — change a value, e.g. `log_level` from `"INFO"` to `"DEBUG"`
5. **Validate** the new version, then **Activate** it
6. Within 5 seconds, watch the browser dashboard update the changed row (highlighted yellow)
7. The **Change History** section shows the diff: `log_level: "INFO" → "DEBUG"`

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Live config dashboard (browser) |
| `GET /config` | Current config as JSON (payload, ETag, layers, connection status) |
| `GET /changes` | Last 20 config diffs as JSON |
