#!/bin/bash

# Compile any assets
yarn build
# Autocompile on changes
yarn watch &
# Run flask development server
flask run --host=0.0.0.0 --port=3000
