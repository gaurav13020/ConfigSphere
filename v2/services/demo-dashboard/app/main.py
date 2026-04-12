from __future__ import annotations

import os

import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse


def demo_targets() -> list[tuple[str, str]]:
    raw = os.getenv("DEMO_TARGETS", "")
    targets: list[tuple[str, str]] = []
    for item in [entry.strip() for entry in raw.split(",") if entry.strip()]:
        if "=" not in item:
            continue
        label, url = item.split("=", 1)
        targets.append((label.strip(), url.strip()))
    return targets


app = FastAPI(title="ConfigSphere Demo Dashboard")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/overview")
async def overview() -> dict:
    targets = demo_targets()
    results = []
    async with httpx.AsyncClient(timeout=5.0) as client:
        for label, url in targets:
            try:
                response = await client.get(url)
                response.raise_for_status()
                payload = response.json()
                payload["targetLabel"] = label
                results.append(payload)
            except Exception as exc:  # noqa: BLE001
                results.append(
                    {
                        "serviceAlias": label,
                        "deliveryServiceName": "unknown",
                        "error": str(exc),
                        "instances": [],
                    }
                )
    return {"services": results}


@app.post("/api/refresh")
async def refresh_target(target: str) -> dict:
    targets = dict(demo_targets())
    target_url = targets.get(target)
    if not target_url:
        return {"ok": False, "error": f"Unknown target '{target}'"}

    refresh_url = target_url.removesuffix("/config") + "/refresh"
    async with httpx.AsyncClient(timeout=8.0) as client:
        try:
            response = await client.post(refresh_url)
            response.raise_for_status()
            payload = response.json()
            payload["targetLabel"] = target
            return {"ok": True, "service": payload}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc), "target": target}


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>ConfigSphere Realtime Config Fetch</title>
    <style>
      :root {
        --bg-top: #f8fbff;
        --bg-bottom: #eef2ff;
        --card: rgba(255,255,255,.96);
        --panel: rgba(255,255,255,.9);
        --border: rgba(91,77,245,.12);
        --text: #0f172a;
        --muted: #64748b;
        --accent: #5b4df5;
        --accent-soft: rgba(91,77,245,.08);
        --healthy-bg: rgba(34,197,94,.12);
        --healthy-fg: #15803d;
        --error-bg: rgba(239,68,68,.12);
        --error-fg: #b91c1c;
        --code-bg: #0f172a;
        --code-fg: #e2e8f0;
      }
      * { box-sizing: border-box; }
      body { margin:0; font-family: ui-sans-serif, system-ui, sans-serif; background: linear-gradient(180deg,var(--bg-top) 0%,var(--bg-bottom) 100%); color:var(--text); }
      .page { padding: 32px; }
      .hero { display:flex; justify-content:space-between; gap:24px; align-items:flex-start; margin-bottom:24px; }
      .hero h1 { font-size: 52px; margin:0 0 8px; }
      .hero p { margin:0; color:var(--muted); max-width:860px; font-size:20px; line-height:1.5; }
      .toolbar { display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
      .status { padding:12px 16px; border-radius:16px; background:#fff; box-shadow:0 10px 30px rgba(15,23,42,.08); color:#475569; }
      .error-banner { margin:0 0 20px; padding:14px 18px; border-radius:18px; background:rgba(239,68,68,.1); color:#991b1b; border:1px solid rgba(239,68,68,.18); display:none; }
      .button { border:none; cursor:pointer; border-radius:16px; padding:12px 16px; font-weight:800; font-size:14px; }
      .button:disabled { opacity:.6; cursor:not-allowed; }
      .button-primary { background:var(--accent); color:#fff; }
      .button-secondary { background:#fff; color:#4338ca; border:1px solid rgba(91,77,245,.18); }
      .button-small { padding:8px 12px; border-radius:12px; font-size:13px; }
      .services { display:grid; gap:24px; }
      .service-card { background:var(--card); border:1px solid var(--border); border-radius:32px; padding:24px; box-shadow:0 18px 45px rgba(91,77,245,.08); }
      .service-head { display:flex; justify-content:space-between; gap:20px; align-items:flex-start; margin-bottom:18px; }
      .service-head h2 { margin:0 0 8px; font-size:32px; }
      .meta { color:var(--muted); }
      .pill-row { display:flex; flex-wrap:wrap; gap:10px; }
      .pill { display:inline-flex; align-items:center; gap:8px; padding:10px 14px; border-radius:999px; background:var(--accent-soft); color:#4338ca; font-weight:700; }
      .tree-wrap { display:grid; gap:12px; }
      .tree-node { background:var(--panel); border:1px solid rgba(148,163,184,.16); border-radius:24px; padding:18px; }
      .node-head { display:flex; justify-content:space-between; gap:16px; align-items:flex-start; }
      .node-toggle { display:flex; align-items:center; gap:10px; cursor:pointer; background:none; border:none; padding:0; color:inherit; text-align:left; font:inherit; }
      .node-name { font-size:24px; font-weight:800; }
      .node-path { color:var(--muted); font-size:14px; margin-top:4px; }
      .subtree { margin-top:14px; margin-left:28px; padding-left:18px; border-left:2px solid rgba(91,77,245,.12); display:grid; gap:12px; }
      .badges { display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; }
      .badge { display:inline-block; padding:6px 10px; border-radius:999px; font-size:12px; font-weight:700; text-transform:uppercase; }
      .healthy { background:var(--healthy-bg); color:var(--healthy-fg); }
      .error { background:var(--error-bg); color:var(--error-fg); }
      .muted-badge { background:rgba(15,23,42,.06); color:#334155; }
      .instance-list { margin-top:16px; display:grid; gap:12px; }
      .instance-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:12px; }
      .instance-card { border-radius:22px; border:1px solid rgba(148,163,184,.16); background:#fff; padding:14px 16px; }
      .instance-card.selected { border-color: rgba(91,77,245,.4); box-shadow:0 12px 24px rgba(91,77,245,.12); }
      .instance-select { width:100%; text-align:left; background:none; border:none; padding:0; cursor:pointer; color:inherit; font:inherit; }
      .row { display:flex; justify-content:space-between; gap:12px; align-items:center; margin-bottom:8px; }
      .detail { margin-top:12px; border-radius:24px; border:1px solid rgba(91,77,245,.14); background:rgba(91,77,245,.04); padding:18px; }
      .detail h4 { margin:0 0 8px; font-size:20px; }
      pre { margin:8px 0 0; padding:16px; border-radius:18px; background:var(--code-bg); color:var(--code-fg); overflow:auto; font-size:13px; }
      .hidden { display:none; }
      .empty { color:#94a3b8; }
      @media (max-width: 900px) {
        .page { padding:20px; }
        .hero { flex-direction:column; }
        .hero h1 { font-size:40px; }
        .service-head { flex-direction:column; }
        .subtree { margin-left:14px; padding-left:12px; }
      }
    </style>
  </head>
  <body>
    <div class="page">
      <div class="hero">
        <div>
          <h1>Realtime Config Fetch</h1>
          <p>Live view of dummy service groups polling ConfigSphere delivery. Expand the hierarchy, refresh specific instances, and click an instance to inspect its exact in-memory config.</p>
        </div>
        <div class="toolbar">
          <button class="button button-primary" id="refreshAllButton" type="button">Refresh all</button>
          <div class="status" id="lastRefresh">Loading instance state...</div>
        </div>
      </div>
      <div class="error-banner" id="errorBanner"></div>
      <div class="services" id="servicesRoot"></div>
    </div>
    <script>
      const servicesRoot = document.getElementById('servicesRoot');
      const refreshAllButton = document.getElementById('refreshAllButton');
      const lastRefresh = document.getElementById('lastRefresh');
      const errorBanner = document.getElementById('errorBanner');

      let currentServices = [];
      let expandedKeys = new Set();
      let selectedInstanceId = null;

      const escapeHtml = (value) => String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');

      const setStatus = (message) => {
        lastRefresh.textContent = message;
      };

      const showError = (message) => {
        errorBanner.textContent = message;
        errorBanner.style.display = 'block';
      };

      const clearError = () => {
        errorBanner.textContent = '';
        errorBanner.style.display = 'none';
      };

      const formatTime = (value) => value ? new Date(value).toLocaleTimeString() : 'never';
      const shortVersion = (value) => value ? String(value).slice(0, 8) : 'pending';

      const captureExpandedState = () => {
        expandedKeys = new Set(
          Array.from(document.querySelectorAll('[data-node-key][data-open="true"]'))
            .map((element) => element.getAttribute('data-node-key'))
            .filter(Boolean)
        );
      };

      const summarizeInstances = (instances) => {
        const healthyCount = instances.filter((instance) => instance.status === 'healthy').length;
        const errorCount = instances.filter((instance) => instance.status !== 'healthy').length;
        const latestUpdate = instances
          .map((instance) => instance.last_update_at)
          .filter(Boolean)
          .sort()
          .at(-1) || null;
        return { total: instances.length, healthyCount, errorCount, latestUpdate };
      };

      const buildHierarchy = (services) => {
        const groups = new Map();

        for (const service of services) {
          const serviceName = service.deliveryServiceName || service.serviceAlias || service.targetLabel || 'unknown';
          if (!groups.has(serviceName)) {
            groups.set(serviceName, {
              serviceName,
              aliases: new Set(),
              errors: [],
              root: { name: 'service', path: serviceName, children: new Map(), instances: [] },
            });
          }

          const group = groups.get(serviceName);
          if (service.serviceAlias) {
            group.aliases.add(service.serviceAlias);
          }
          if (service.error) {
            group.errors.push(service.error);
          }

          for (const instance of (service.instances || [])) {
            const parts = String(instance.path || '/').split('/').filter(Boolean);
            let cursor = group.root;
            let currentPath = '';
            for (const part of parts) {
              currentPath += `/${part}`;
              if (!cursor.children.has(part)) {
                cursor.children.set(part, {
                  name: part,
                  path: currentPath,
                  children: new Map(),
                  instances: [],
                });
              }
              cursor = cursor.children.get(part);
            }
            cursor.instances.push(instance);
          }
        }

        return Array.from(groups.values());
      };

      const renderInstanceCard = (instance) => {
        const selected = instance.instance_id === selectedInstanceId ? ' selected' : '';
        return `
          <div class="instance-card${selected}">
            <button class="instance-select" type="button" data-instance-id="${escapeHtml(instance.instance_id)}">
              <div class="row">
                <strong>${escapeHtml(instance.instance_name)}</strong>
                <span class="badge ${instance.status === 'healthy' ? 'healthy' : 'error'}">${escapeHtml(instance.status)}</span>
              </div>
              <div class="meta">Path ${escapeHtml(instance.path)} • Version ${escapeHtml(shortVersion(instance.version_id))} • Tree ${escapeHtml(instance.tree_version ?? '-')}</div>
              <div class="meta">Last poll ${escapeHtml(formatTime(instance.last_poll_at))} • Last config update ${escapeHtml(formatTime(instance.last_update_at))}</div>
              <div class="meta">Source ${escapeHtml(instance.service_alias)}</div>
              ${instance.error_message ? `<div class="meta">Error: ${escapeHtml(instance.error_message)}</div>` : ''}
            </button>
            <div class="row" style="margin-top:10px;">
              <div class="meta">${instance.instance_id === selectedInstanceId ? 'Selected' : 'Click to inspect config'}</div>
              <button class="button button-secondary button-small" type="button" data-refresh-target="${escapeHtml(instance.service_alias)}">Refresh</button>
            </div>
          </div>
        `;
      };

      const renderSelectedInstance = (instances) => {
        const selected = instances.find((instance) => instance.instance_id === selectedInstanceId);
        if (!selected) {
          return '';
        }

        return `
          <div class="detail">
            <h4>${escapeHtml(selected.instance_name)}</h4>
            <div class="meta">Path ${escapeHtml(selected.path)} • Version ${escapeHtml(shortVersion(selected.version_id))} • Tree ${escapeHtml(selected.tree_version ?? '-')}</div>
            <div class="meta">Last poll ${escapeHtml(formatTime(selected.last_poll_at))} • Last config update ${escapeHtml(formatTime(selected.last_update_at))}</div>
            <pre>${escapeHtml(JSON.stringify(selected.config || {}, null, 2))}</pre>
          </div>
        `;
      };

      const renderNode = (node, depth = 0) => {
        const nodeKey = `${node.path}|${depth}`;
        const childNodes = Array.from(node.children.values()).sort((a, b) => a.name.localeCompare(b.name));
        const summary = summarizeInstances(node.instances);
        const open = expandedKeys.size ? expandedKeys.has(nodeKey) : depth < 2;
        const subtreeClass = open ? 'subtree' : 'subtree hidden';

        return `
          <div class="tree-node" data-node-key="${escapeHtml(nodeKey)}" data-open="${open ? 'true' : 'false'}">
            <div class="node-head">
              <button class="node-toggle" type="button" data-toggle-node="${escapeHtml(nodeKey)}">
                <span>${open ? '▾' : '▸'}</span>
                <span>
                  <div class="node-name">${escapeHtml(node.name)}</div>
                  <div class="node-path">${escapeHtml(node.path)}</div>
                </span>
              </button>
              <div class="badges">
                ${summary.total ? `<span class="badge healthy">${summary.total} instance${summary.total === 1 ? '' : 's'}</span>` : ''}
                ${childNodes.length ? `<span class="badge muted-badge">${childNodes.length} child node${childNodes.length === 1 ? '' : 's'}</span>` : ''}
              </div>
            </div>
            ${node.instances.length ? `
              <div class="instance-list">
                <div class="row">
                  <div class="meta">Instances at this node: ${summary.total}</div>
                  <div class="badges">
                    <span class="badge healthy">${summary.healthyCount} healthy</span>
                    ${summary.errorCount ? `<span class="badge error">${summary.errorCount} error</span>` : ''}
                    <span class="badge muted-badge">${summary.latestUpdate ? `last config update ${escapeHtml(formatTime(summary.latestUpdate))}` : 'no config yet'}</span>
                  </div>
                </div>
                <div class="instance-grid">
                  ${node.instances.map(renderInstanceCard).join('')}
                </div>
                ${renderSelectedInstance(node.instances)}
              </div>
            ` : ''}
            <div class="${subtreeClass}">
              ${childNodes.map((child) => renderNode(child, depth + 1)).join('')}
            </div>
          </div>
        `;
      };

      const renderServices = () => {
        const grouped = buildHierarchy(currentServices);
        if (!grouped.length) {
          servicesRoot.innerHTML = '<div class="empty">No demo services reported yet.</div>';
          return;
        }

        servicesRoot.innerHTML = grouped.map((group) => {
          const allInstances = [];
          const collect = (node) => {
            allInstances.push(...node.instances);
            node.children.forEach(collect);
          };
          collect(group.root);
          const summary = summarizeInstances(allInstances);
          const topNodes = Array.from(group.root.children.values()).sort((a, b) => a.name.localeCompare(b.name));

          return `
            <section class="service-card">
              <div class="service-head">
                <div>
                  <h2>${escapeHtml(group.serviceName)}</h2>
                  <div class="meta">Demo containers: ${escapeHtml(Array.from(group.aliases).sort().join(', '))}</div>
                </div>
                <div class="pill-row">
                  <span class="pill">${summary.total} total instances</span>
                  <span class="pill">${summary.healthyCount} healthy</span>
                  <span class="pill">${summary.errorCount} error</span>
                </div>
              </div>
              ${group.errors.length ? `<div class="meta">Upstream errors: ${escapeHtml(group.errors.join(' | '))}</div>` : ''}
              <div class="tree-wrap">
                ${topNodes.map((node) => renderNode(node, 0)).join('')}
              </div>
            </section>
          `;
        }).join('');
      };

      const loadOverview = async () => {
        try {
          const response = await fetch('/api/overview');
          const payload = await response.json();
          currentServices = payload.services || [];
          clearError();
          renderServices();
          setStatus(`Last refresh: ${new Date().toLocaleTimeString()}`);
        } catch (error) {
          console.error(error);
          showError(`Initial load failed: ${error?.message || error}`);
        }
      };

      const refreshTarget = async (target) => {
        captureExpandedState();
        setStatus(`Refreshing ${target}...`);
        try {
          const response = await fetch(`/api/refresh?target=${encodeURIComponent(target)}`, { method: 'POST' });
          const payload = await response.json();
          if (!payload.ok) {
            throw new Error(payload.error || `Refresh failed for ${target}`);
          }
          currentServices = currentServices
            .filter((service) => (service.serviceAlias || service.targetLabel) !== target)
            .concat(payload.service);
          clearError();
          renderServices();
          setStatus(`Refreshed ${target} at ${new Date().toLocaleTimeString()}`);
        } catch (error) {
          console.error(error);
          showError(`Refresh failed: ${error?.message || error}`);
        }
      };

      document.addEventListener('click', async (event) => {
        const toggle = event.target.closest('[data-toggle-node]');
        if (toggle) {
          const key = toggle.getAttribute('data-toggle-node');
          const node = document.querySelector(`[data-node-key="${CSS.escape(key)}"]`);
          if (node) {
            const open = node.getAttribute('data-open') === 'true';
            node.setAttribute('data-open', open ? 'false' : 'true');
            if (open) expandedKeys.delete(key); else expandedKeys.add(key);
            renderServices();
          }
          return;
        }

        const selectButton = event.target.closest('[data-instance-id]');
        if (selectButton) {
          captureExpandedState();
          const instanceId = selectButton.getAttribute('data-instance-id');
          selectedInstanceId = selectedInstanceId === instanceId ? null : instanceId;
          renderServices();
          return;
        }

        const refreshButton = event.target.closest('[data-refresh-target]');
        if (refreshButton) {
          const target = refreshButton.getAttribute('data-refresh-target');
          if (!target) return;
          refreshButton.disabled = true;
          try {
            await refreshTarget(target);
          } finally {
            refreshButton.disabled = false;
          }
        }
      });

      refreshAllButton.addEventListener('click', async () => {
        refreshAllButton.disabled = true;
        captureExpandedState();
        try {
          for (const service of currentServices) {
            const target = service.serviceAlias || service.targetLabel;
            if (target) {
              await refreshTarget(target);
            }
          }
        } finally {
          refreshAllButton.disabled = false;
        }
      });

      loadOverview();
    </script>
  </body>
</html>
"""
