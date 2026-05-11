#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env.droplet"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.droplet.yml"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}"
  echo "Copy .env.droplet.example to .env.droplet and update the values first."
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed."
  echo "Install Docker Engine and the Docker Compose plugin on the droplet first."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose plugin is not available."
  exit 1
fi

cd "${ROOT_DIR}"

echo "Building and starting ConfigSphere on the droplet..."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d --build

echo
echo "Stack started. Useful URLs:"
echo "Frontend:       $(grep '^VITE_CONTROL_PLANE_URL=' "${ENV_FILE}" >/dev/null 2>&1 && grep '^VITE_CONTROL_PLANE_URL=' "${ENV_FILE}" | cut -d= -f2 | sed 's|:8100$|:3001|' || echo 'http://YOUR_DROPLET_IP:3001')"
echo "Control Plane:  http://YOUR_DROPLET_IP:8100"
echo "Delivery:       http://YOUR_DROPLET_IP:8101"
echo "Keycloak:       http://YOUR_DROPLET_IP:8080"
echo
echo "To check status:"
echo "docker compose --env-file ${ENV_FILE} -f ${COMPOSE_FILE} ps"
