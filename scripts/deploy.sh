#!/usr/bin/env bash
# Build and (re)start the production stack. Safe to re-run for redeploys —
# `git pull` picks up new code, `up -d --build` only rebuilds changed images.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "Missing .env — copy .env.production.example to .env and fill it in first."
  exit 1
fi

echo "== Pulling latest code =="
git pull

echo "== Building and starting containers =="
docker compose -f docker-compose.prod.yml up -d --build

echo "== Waiting for backend to become healthy =="
sleep 5
docker compose -f docker-compose.prod.yml ps

echo ""
echo "== First deploy only: run this once to create tables + the first admin user =="
echo "  docker compose -f docker-compose.prod.yml exec backend python -m app.init_db"
echo ""
echo "Deploy complete."
