# OpenOversight

OpenOversight is a Lucy Parson Labs project to improve police accountability through public and crowdsourced data. We maintain a database of police officers and provide a set of tools including facial recognition capabilities and digital line-ups to help people identify police officers they would like to file a complaint on.

As a proof of concept, OpenOversight currently uses the Chicago Police Department but this infrastructure will be used to extent the project to other cities where additional oversight is needed. Interested in helping bring OpenOversight to your city? Email us at openoversight@redshiftzero.com.  

Our technology stack:
 * We use Python 2.7 as we have deps not yet Python 3 compatible 
 * Machine learning and facial recognition: openface, opencv
 * Web frontend: Flask
 * Database backend: psycopg2, PostgreSQL
 * ETL toolchain: pandas, sqlalchemy

This project is written and maintained by @redshiftzero with contributions welcome. If you would like to contribute code or documentation, please see our contributing guide. If you prefer to contribute in other ways, please submit images to our platform or use our crowd-sourced human labeling tool to help build training datasets.

## Issues

Please use [our issue tracker](https://github.com/lucyparsons/OpenOversight//issues/new) to submit issues or suggestions. 

## Documentation

TODO

## Components

* `OpenOversight`: the main web application and facial recognition code
* `socmint`: scripts for gathering images from social media, currently just official police accounts
* `etl`: scripts for taking primarily data dumps from FOIA and other organizations, cleaning them, and uploading them into our database 
* `database`: details of how our officer and image databases are set up 

## Data Collection

* Public datasets: Download recently tweeted photos from official police accounts. 
* Linking dataset: In order to provide identities of officers, we need the roster of all police officers as well as their star number history (if star numbers change upon promotion). 
* Solicitation from our users: Get users to submit images of police officers they take or find online to augment our training data.
* Officer activity information: Acquired through FOIA
