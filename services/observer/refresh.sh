#!/bin/bash
# Regenerates the mainnet-observer charts from the node's REST API.
# OBSERVER_DIR must contain data/, csv/ and a clone of 0xB10C/mainnet-observer.
set -e
OBSERVER_DIR="${OBSERVER_DIR:-$HOME/observer}"
REST_HOST="${REST_HOST:-172.18.0.3}"

docker run --rm --name mainnet-observer-backend --network bitcoin_network \
  -v "$OBSERVER_DIR/data:/data" -v "$OBSERVER_DIR/csv:/csv" \
  mainnet-observer-backend --rest-host "$REST_HOST" --rest-port 8332 \
  --database-path /data/stats.db --csv-path /csv --start-height 1

cp "$OBSERVER_DIR"/csv/*.csv "$OBSERVER_DIR/mainnet-observer/frontend/static/csv/"
docker build -t mainnet-observer-frontend "$OBSERVER_DIR/mainnet-observer/frontend"

docker rm -f mainnet-observer-frontend 2>/dev/null || true
docker run -d --name mainnet-observer-frontend --restart unless-stopped -p 8889:80 mainnet-observer-frontend
