#!/bin/bash

# Find the process ID of the running server
PID=$(ps aux | grep "python main.py" | grep -v grep | awk '{print $2}')

if [ -n "$PID" ]; then
  echo "Stopping server with PID $PID"
  kill $PID
  sleep 2
fi

# Activate the virtual environment and start the server
echo "Starting server..."
source .venv/bin/activate
python main.py