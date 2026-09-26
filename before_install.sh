#!/bin/bash
# CodeDeploy BeforeInstall hook - prepares the instance before the new
# application revision is copied in.
set -euxo pipefail

dnf install -y python3 python3-pip

# Clean any previous revision so redeploys start fresh.
rm -rf /opt/orderservice/app /opt/orderservice/venv
mkdir -p /opt/orderservice/app
