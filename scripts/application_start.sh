#!/bin/bash
# CodeDeploy ApplicationStart hook.
set -euxo pipefail

systemctl start orderservice.service
