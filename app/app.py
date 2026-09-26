"""
DT_Workshop - Order Service

A small 3-tier demo application (ALB -> EC2/Flask -> RDS MySQL) used to
demonstrate AWS DevOps Agent, AWS Continuum, and AWS FinOps Agent.

Configuration is read from environment variables (set by the CodeDeploy
lifecycle scripts, see scripts/before_install.sh):

  DB_HOST         - RDS endpoint address
  DB_NAME         - database name
  DB_SECRET_ARN   - Secrets Manager ARN holding {"username":..., "password":...}
  AWS_REGION      - region for the boto3 Secrets Manager client
"""
import logging
import os
import time
from datetime import datetime, timezone

import boto3
import pymysql
from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orderservice")

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "")
DB_NAME = os.environ.get("DB_NAME", "ordersdb")
DB_SECRET_ARN = os.environ.get("DB_SECRET_ARN", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

_db_credentials_cache = None


def get_db_credentials():
    """Fetch DB username/password from Secrets Manager, caching for process lifetime."""
    global _db_credentials_cache
    if _db_credentials_cache is not None:
        return _db_credentials_cache

    if not DB_SECRET_ARN:
        raise RuntimeError("DB_SECRET_ARN is not set")

    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    response = client.get_secret_value(SecretId=DB_SECRET_ARN)
    import json

    secret = json.loads(response["SecretString"])
    _db_credentials_cache = (secret["username"], secret["password"])
    return _db_credentials_cache


def get_db_connection():
    username, password = get_db_credentials()
    return pymysql.connect(
        host=DB_HOST,
        user=username,
        password=password,
        database=DB_NAME,
        connect_timeout=5,
        cursorclass=pymysql.cursors.DictCursor,
    )


def ensure_schema():
    """Create the orders table if it doesn't already exist. Called at startup."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    item_name VARCHAR(255) NOT NULL,
                    quantity INT NOT NULL,
                    created_at DATETIME NOT NULL
                )
                """
            )
        conn.commit()
    finally:
        conn.close()


@app.route("/health")
def health():
    """ALB target group health check. Deliberately does not touch the DB
    so a database blip doesn't take healthy instances out of rotation."""
    return jsonify(status="ok", service="orderservice", time=datetime.now(timezone.utc).isoformat())


@app.route("/")
def index():
    return jsonify(
        service="DT_Workshop Order Service",
        endpoints=["/health", "/orders (GET, POST)", "/orders/<id> (GET)"],
    )


@app.route("/orders", methods=["GET"])
def list_orders():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, item_name, quantity, created_at FROM orders ORDER BY id DESC LIMIT 50")
            rows = cursor.fetchall()
        return jsonify(orders=rows)
    finally:
        conn.close()


@app.route("/orders", methods=["POST"])
def create_order():
    payload = request.get_json(silent=True) or {}
    item_name = payload.get("item_name")
    quantity = payload.get("quantity")

    if not item_name or not isinstance(quantity, int):
        return jsonify(error="item_name (string) and quantity (int) are required"), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO orders (item_name, quantity, created_at) VALUES (%s, %s, %s)",
                (item_name, quantity, datetime.now(timezone.utc)),
            )
        conn.commit()
        return jsonify(status="created", item_name=item_name, quantity=quantity), 201
    finally:
        conn.close()


@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, item_name, quantity, created_at FROM orders WHERE id = %s", (order_id,))
            row = cursor.fetchone()
        if row is None:
            return jsonify(error="not found"), 404
        return jsonify(order=row)
    finally:
        conn.close()


if __name__ == "__main__":
    # Local/dev entrypoint only. In production, gunicorn runs the app (see orderservice.service).
    for attempt in range(5):
        try:
            ensure_schema()
            break
        except Exception as exc:  # noqa: BLE001
            logger.warning("Schema init failed (attempt %s/5): %s", attempt + 1, exc)
            time.sleep(3)
    app.run(host="0.0.0.0", port=8080)
