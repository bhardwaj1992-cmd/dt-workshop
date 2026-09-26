#!/bin/bash
# CodeDeploy BeforeInstall hook - prepares the instance before the new
# application revision is copied in.
set -euxo pipefail

dnf install -y python3 python3-pip

mkdir -p /opt/orderservice
