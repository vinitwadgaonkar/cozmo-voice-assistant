#!/bin/bash

# Setup environment
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Load .env if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the server
cd "$(dirname "$0")"
python server/main.py dev

