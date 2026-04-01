"""
payment-svc — Dummy microservice demonstrating real-time config polling via ConfigSphere SDK.

Starts a Flask web server on port 5001 with:
  GET /          — Browser dashboard (auto-refreshes every 3s)
  GET /config    — JSON: current config, connection status, ETag, layers
  GET /changes   — JSON: last 20 config diffs with timestamps
"""

import json
import logging
import os
import threading
from collections import deque
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template

from configsphere import ConfigSphereClient, SDKConfig, ScopeParams

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)-20s] %(levelname)s: %(message)s",
)
logging.getLogger("configsphere").setLevel(logging.DEBUG)
log = logging.getLogger("payment-svc")

# ── ConfigSphere SDK ───────────────────────────────────────────────────────────
_server_url = os.environ.get("CONFIGSPHERE_URL", "http://localhost:8000/api/v1")

sdk_config = SDKConfig(
    server_url=_server_url,
    scope=ScopeParams(service_name="payment-svc"),
    poll_interval_sec=5,  # Fast poll so demo changes show up quickly
)

_changes: deque = deque(maxlen=20)
_changes_lock = threading.Lock()


def on_config_change(diff: dict) -> None:
    """Called by the SDK poller thread whenever resolved config changes."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "diff": diff,
    }
    with _changes_lock:
        _changes.appendleft(entry)
    log.info("Config changed: %s", json.dumps(diff, default=str))


cs_client = ConfigSphereClient(sdk_config)
cs_client.on_change(on_config_change)
cs_client.start()
log.info("ConfigSphere client started — polling every %ss", sdk_config.poll_interval_sec)

# ── Flask app ──────────────────────────────────────────────────────────────────
app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/config")
def get_config():
    resolved = cs_client.get_config()
    return jsonify({
        "connected": cs_client.is_connected(),
        "etag": cs_client.etag,
        "last_updated": cs_client.last_updated.isoformat() if cs_client.last_updated else None,
        "payload": cs_client.get_all(),
        "layers": [
            {
                "scope_level": layer.scope_level,
                "key": layer.key,
                "version_number": layer.version_number,
                "config_version_id": layer.config_version_id,
            }
            for layer in resolved.layers
        ] if resolved else [],
    })


@app.route("/changes")
def get_changes():
    with _changes_lock:
        return jsonify(list(_changes))


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)
    finally:
        cs_client.close()
        log.info("ConfigSphere client closed")
