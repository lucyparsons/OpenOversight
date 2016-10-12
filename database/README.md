# Database Setup

## Schema/Table Creation

Create with `OpenOversight/create_db.py`

## Database Diagram

![](oodb_with_rawimg_table.jpg)

(if you want to nicely typeset this please do - and ideally in a way that enables us to easily make edits (e.g. LaTeX or graphviz))

## Populating from Raw Data

Everything here assumes that you executed the ETL scripts in `etl` to load the raw data into `public`. Once you've done that you can get the data into the form that the webapp expects using the following scripts:

```
psql -f populate_officer_roster_and_assignment.sql
```

Note: the remaining SQL scripts in here are deprecated
