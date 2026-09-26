#!/bin/bash
# CodeDeploy ApplicationStop hook - runs before new revision files are copied in.
set -e

if systemctl list-unit-files orderservice.service >/dev/null 2>&1; then
  systemctl stop orderservice.service || true
fi
