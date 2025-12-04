#!/usr/bin/env bash
set -euo pipefail

SMOKE_TIMEOUT_SECONDS=${SMOKE_TIMEOUT_SECONDS:-60}
SMOKE_POLL_INTERVAL=${SMOKE_POLL_INTERVAL:-5}
SMOKE_LOGFILE=${SMOKE_LOGFILE:-tests/e2e/smoke-logs.txt}
DEBUG=${SMOKE_DEBUG:-false}

echo "Starting smoke E2E checks..."

rm -f "$SMOKE_LOGFILE"

if command -v docker >/dev/null 2>&1; then
  echo "Docker found — attempting to bring up docker-compose services"
  if [ -f docker-compose.yml ]; then
    docker compose up -d --build
    echo "Waiting for services to become healthy (timeout ${SMOKE_TIMEOUT_SECONDS}s)"

    elapsed=0
    success=false
    while [ $elapsed -lt $SMOKE_TIMEOUT_SECONDS ]; do
      if curl --fail --silent http://localhost:8000/healthz >/dev/null 2>&1; then
        echo "API /healthz OK"
        success=true
        break
      fi
      sleep $SMOKE_POLL_INTERVAL
      elapsed=$((elapsed + SMOKE_POLL_INTERVAL))
      echo "Waited ${elapsed}s..."
    done

    if [ "$success" != true ]; then
      echo "API /healthz FAILED after ${SMOKE_TIMEOUT_SECONDS}s"
      echo "Collecting docker-compose logs to $SMOKE_LOGFILE"
      docker compose logs --no-color > "$SMOKE_LOGFILE" || true
      docker compose down || true
      echo "Smoke logs written to $SMOKE_LOGFILE"
      exit 2
    fi

    # Basic frontend check (may not be present in all setups)
    if curl --fail --silent http://localhost:3000/ >/dev/null 2>&1; then
      echo "Frontend root OK"
    else
      echo "Frontend root not reachable — continuing (may be SPA build-only)"
    fi

    docker compose down || true
  else
    echo "No docker-compose.yml found; skipping docker-based checks"
  fi
else
  echo "Docker not available on runner; skipping smoke E2E"
fi

echo "Smoke E2E checks completed"
if [[ "$DEBUG" == "true" && -f "$SMOKE_LOGFILE" ]]; then
  echo "--- SMOKE LOGS ---"
  cat "$SMOKE_LOGFILE"
  echo "--- END SMOKE LOGS ---"
fi
