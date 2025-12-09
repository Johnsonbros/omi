#!/bin/bash
set -e

redis-server --daemonize yes --port 6379

cd /home/runner/workspace/zeke-core

python worker.py &
WORKER_PID=$!

python main.py &
BACKEND_PID=$!

cd dashboard
HOST=0.0.0.0 PORT=5000 npm run preview &
FRONTEND_PID=$!

wait $BACKEND_PID $FRONTEND_PID $WORKER_PID
