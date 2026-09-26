#!/bin/bash
# CodeDeploy ValidateService hook - confirms the app is actually serving
# traffic on localhost before CodeDeploy marks the deployment successful.
set -euo pipefail

for i in $(seq 1 10); do
  if curl -sf http://127.0.0.1:8080/health >/dev/null; then
    echo "orderservice is healthy."
    exit 0
  fi
  echo "Waiting for orderservice to become healthy... ($i/10)"
  sleep 3
done

echo "orderservice failed health validation." >&2
exit 1
