#!/usr/bin/env bash
# Create the MinIO buckets the platform expects.
# Idempotent. Safe to re-run.
set -euo pipefail

ENDPOINT=${MINIO_ENDPOINT:-http://localhost:9000}
USER=${MINIO_ROOT_USER:-minioadmin}
PASS=${MINIO_ROOT_PASSWORD:-minioadmin}

if ! command -v mc >/dev/null 2>&1; then
    echo "mc (minio client) not installed. install with 'brew install minio/stable/mc' or download from min.io"
    exit 1
fi

mc alias set local "$ENDPOINT" "$USER" "$PASS" >/dev/null

for bucket in mlops-artifacts mlops-features mlops-monitoring; do
    if mc ls "local/$bucket" >/dev/null 2>&1; then
        echo "ok: $bucket already exists"
    else
        mc mb "local/$bucket"
        echo "created: $bucket"
    fi
done

# write a marker so we can tell from grafana whether minio is provisioned
echo "provisioned at $(date -u +%FT%TZ)" | mc pipe local/mlops-artifacts/.provisioned
