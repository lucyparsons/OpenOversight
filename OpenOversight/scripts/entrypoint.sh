#!/bin/bash
if [ "${DOCKER_BUILD_ENV:-}" == "production" ]; then
    # Compile any assets
    npm run-script build
    # Copy static assets into NEW folder, specifically at runtime
    cp -R /usr/src/app/OpenOversight/app/static/* /usr/src/app/OpenOversight/static/
    gunicorn -w 4 -b 0.0.0.0:3000 OpenOversight.app:app
else
    yarn build
    yarn watch &
    flask run --host=0.0.0.0 --port=3000
fi
