#!/bin/bash
set -e

# Start Celery worker + beat (combined, single lightweight worker)
celery -A app.workers.celery_app worker \
  --beat \
  --loglevel=info \
  --concurrency=1 \
  --max-tasks-per-child=50 &
CELERY_PID=$!

# Start FastAPI
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers 1 &
UVICORN_PID=$!

# Exit if either process dies
wait -n $CELERY_PID $UVICORN_PID
EXIT_CODE=$?
kill $CELERY_PID $UVICORN_PID 2>/dev/null || true
exit $EXIT_CODE
