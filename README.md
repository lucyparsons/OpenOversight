![](docs/img/lpl-logo.png)

# OpenOversight (Seattle Fork) [![Build Status](https://travis-ci.org/lucyparsons/OpenOversight.svg?branch=develop)](https://travis-ci.org/lucyparsons/OpenOversight) [![Coverage Status](https://coveralls.io/repos/github/lucyparsons/OpenOversight/badge.svg?branch=develop)](https://coveralls.io/github/lucyparsons/OpenOversight?branch=develop) [![Documentation Status](https://readthedocs.org/projects/openoversight/badge/?version=latest)](https://openoversight.readthedocs.io/en/latest/?badge=latest) [![Join the chat at https://gitter.im/OpenOversight/Lobby](https://badges.gitter.im/OpenOversight/Lobby.svg)](https://gitter.im/OpenOversight/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

OpenOversight is a Lucy Parsons Labs project to improve law enforcement accountability through public and crowdsourced data. We maintain a database of officer demographic information and provide digital galleries of photographs. This is done to help people identify law enforcement officers for filing complaints and in order for the public to see work-related information about law enforcement officers that interact with the public.

This repository represents the **Seattle fork** of the original project. For more info, see the [old README](README_OLD.md) or [the original repository](https://github.com/lucyparsons/OpenOversight/)

## Development

To run the project locally:
1. [Install `just`](https://github.com/casey/just)
1. Copy the sample data to the data folder mounted by the project `cp database/sample_init_data.csv data/init_data.csv`.
1. Run `just fresh-start` to spin up the database and insert the initial data.
1. Run `just up` and visit http://localhost:3000!


## Deployment

Please see the [DEPLOY.md](/DEPLOY.md) file for deployment instructions.

The same `just` commands can be used to deploy production.
The `docker-compose-prod.yml` file defines the minimum services for running in production.
In order to use this file, set the `IS_PROD` environment variable to `true`.
This will run all commands using the prod docker file.
