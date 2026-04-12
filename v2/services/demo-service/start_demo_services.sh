#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V2_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${V2_ROOT}"

export DEMO_CONFIG_TOKEN_01='cfgsdk_tHC2OomT9LK2xNigQZ3g-fmz47-Hs-wfdQLZBs5GgdM'
export DEMO_CONFIG_TOKEN_02='cfgsdk_tHC2OomT9LK2xNigQZ3g-fmz47-Hs-wfdQLZBs5GgdM'
export DEMO_CONFIG_TOKEN_03='cfgsdk_tHC2OomT9LK2xNigQZ3g-fmz47-Hs-wfdQLZBs5GgdM'
export DEMO_CONFIG_TOKEN_04='cfgsdk_tHC2OomT9LK2xNigQZ3g-fmz47-Hs-wfdQLZBs5GgdM'
export DEMO_CONFIG_TOKEN_05='cfgsdk_tHC2OomT9LK2xNigQZ3g-fmz47-Hs-wfdQLZBs5GgdM'
export DEMO_CONFIG_TOKEN_06='cfgsdk_tHC2OomT9LK2xNigQZ3g-fmz47-Hs-wfdQLZBs5GgdM'
export DEMO_CONFIG_TOKEN_07='cfgsdk_tHC2OomT9LK2xNigQZ3g-fmz47-Hs-wfdQLZBs5GgdM'
export DEMO_CONFIG_TOKEN_08='cfgsdk_tHC2OomT9LK2xNigQZ3g-fmz47-Hs-wfdQLZBs5GgdM'
export DEMO_CONFIG_TOKEN_09='cfgsdk_tHC2OomT9LK2xNigQZ3g-fmz47-Hs-wfdQLZBs5GgdM'
export DEMO_CONFIG_TOKEN_10='cfgsdk_tHC2OomT9LK2xNigQZ3g-fmz47-Hs-wfdQLZBs5GgdM'

MODE="${1:-light}"

if [[ "${MODE}" == "full" ]]; then
  echo "Starting full realtime demo stack with 10 demo service groups and the dashboard..."
  docker compose -f docker-compose.demo.yml up --build
else
  echo "Starting light realtime demo stack with one demo service group and the dashboard..."
  echo "Use './services/demo-service/start_demo_services.sh full' for the full 110-instance demo."
  docker compose -f docker-compose.demo.yml up --build demo-service-01 demo-dashboard
fi

echo
echo "Dashboard URL: http://localhost:8300"
