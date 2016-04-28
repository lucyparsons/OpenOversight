# Database Setup

## Roster

The backend is an Amazon RDS PostgreSQL database.

## Image Storage

We store the officer images on Amazon S3, and have a table in PostgreSQL that keeps track of which officers each image is associated with. Each police department has an S3 bucket with a series of directories each named for an officer's `oo_id` inside. 
