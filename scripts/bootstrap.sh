#!/usr/bin/env bash
# Local stack bootstrap. Brings up postgres/redis/minio/mlflow/prefect,
# runs migrations and seeds the platform metadata.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    cp .env.example .env
    echo "wrote .env from example. tweak before re-running if needed."
fi

docker compose up -d postgres redis minio
echo "waiting for postgres..."
until docker compose exec -T postgres pg_isready -U feast > /dev/null 2>&1; do
    sleep 2
done

docker compose exec -T postgres psql -U feast -c "CREATE DATABASE mlflow;" || true
docker compose exec -T postgres psql -U feast -c "CREATE DATABASE prefect;" || true
docker compose exec -T postgres psql -U feast -c "CREATE DATABASE feast_registry;" || true

# minio bucket
docker compose run --rm --entrypoint sh minio -c '
mc alias set local http://minio:9000 minioadmin minioadmin
mc mb -p local/mlops-artifacts || true
'

docker compose up -d mlflow prefect prometheus pushgateway grafana dashboard

echo "stack up. dashboard: http://localhost:8080"
echo "mlflow:    http://localhost:5000"
echo "prefect:   http://localhost:4200"
echo "grafana:   http://localhost:3000 (admin/admin)"
