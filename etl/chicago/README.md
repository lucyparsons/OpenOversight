## Roster

The current roster of officers acquired by submitting a FOIA request for:

> The current roster of sworn officers in the Chicago Police Department.
> These documents should be sufficient to show:
> * Names of each sworn police officer. There should be at least 13976 rows in this dataset.
> * Current badge number
> * Current rank
> * Gender
> * Race
> * Date of employment

We upload to our database with `roster.load()`.

We do not use star numbers as the primary key due to the fact that they change - see `setup_ids.sql`.  

## Data from Invisible Institute

[Invisible Institute](http://invisible.institute/) is a Chicago-based non profit that has published an open database of police complaints in the city. We also use their data, which includes data on star numbers in the city, to augment our roster. We got two files which we upload with `invisinst.load()` and `assignments.load()`.
