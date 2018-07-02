#!/bin/bash
if [ "${HMR:-}" == "1" ]; then
    yarn watch --hmr-port 3001 &
else
    yarn build
fi
flask run --host=0.0.0.0 --port=3000
