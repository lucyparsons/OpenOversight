#!/bin/bash
if [ "${DOCKER_BUILD_ENV:-}" == "production" ]; then
    flask run --host=0.0.0.0 --port=3000
else
    # forwarding port 9000 to minio for local S3 bucket
    scripts/minio_forward.sh &
    yarn build
    yarn watch &
    flask run --host=0.0.0.0 --port=3000
fi
