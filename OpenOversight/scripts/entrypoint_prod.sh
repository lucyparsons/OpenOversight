#!/bin/bash

# Compile any assets
yarn build
# Copy static assets into NEW folder, specifically at runtime
cp -R /usr/src/app/OpenOversight/app/static/* /usr/src/app/OpenOversight/static/
# Run flask server via gunicorn
gunicorn -w 4 -b 0.0.0.0:3000 OpenOversight.app:app
