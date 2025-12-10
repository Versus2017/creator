#!/bin/bash

set -e

PORT=${PORT:-8000}
WEB_CONCURRENCY=${WEB_CONCURRENCY:-4}
WEB_WORKER_TYPE=${WEB_WORKER_TYPE:-sync}
WORKER_CONCURRENCY=${WORKER_CONCURRENCY:-4}
WORKER_WORKER_TYPE=${WORKER_WORKER_TYPE:-process}

case $1 in
    web)
        alembic upgrade head
        exec uvicorn creator.app:app --host 0.0.0.0 --port $PORT --workers 6
        ;;
    socketio)
        exec python run_sio.py
        ;;
    worker)
        exec huey_consumer -w $WORKER_CONCURRENCY -k $WORKER_WORKER_TYPE creator.huey_app.huey
        ;;
    -h)
        echo "run components: [web|worker], or any other shell command"
        ;;
    *)
        exec "$@"
        ;;
esac
