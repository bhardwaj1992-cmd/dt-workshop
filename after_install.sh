#!/bin/bash
# CodeDeploy AfterInstall hook - runs after the new application revision has
# been copied to /opt/orderservice/app. Sets up the Python venv, resolves DB
# connection info from SSM Parameter Store, writes the runtime env file,
# and installs/refreshes the systemd unit.
set -euxo pipefail

PROJECT_TAG="DT_Workshop"
APP_DIR="/opt/orderservice"

# Region lookup via IMDSv2 (Amazon Linux 2023 requires a session token for
# instance metadata). Fall back to us-east-1 if the token call fails.
TOKEN="$(curl -s --max-time 3 -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 300" || true)"
REGION="$(curl -s --max-time 3 -H "X-aws-ec2-metadata-token: ${TOKEN}" \
  http://169.254.169.254/latest/meta-data/placement/region || true)"
REGION="${REGION:-us-east-1}"

cd "$APP_DIR"

python3 -m venv venv
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet -r app/requirements.txt

DB_HOST="$(aws ssm get-parameter --name "/${PROJECT_TAG}/db/host" --region "$REGION" --query 'Parameter.Value' --output text)"
DB_NAME="$(aws ssm get-parameter --name "/${PROJECT_TAG}/db/name" --region "$REGION" --query 'Parameter.Value' --output text)"
DB_SECRET_ARN="$(aws ssm get-parameter --name "/${PROJECT_TAG}/db/secret_arn" --region "$REGION" --query 'Parameter.Value' --output text)"

cat > "$APP_DIR/env.conf" <<EOF
DB_HOST=${DB_HOST}
DB_NAME=${DB_NAME}
DB_SECRET_ARN=${DB_SECRET_ARN}
AWS_REGION=${REGION}
EOF

chown -R ec2-user:ec2-user "$APP_DIR"

cp "$APP_DIR/app/orderservice.service" /etc/systemd/system/orderservice.service
systemctl daemon-reload
systemctl enable orderservice.service
