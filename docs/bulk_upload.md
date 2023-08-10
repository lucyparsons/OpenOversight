Using the bulk upload feature
=============================
To facilitate adding rosters of new departments or updating existing
departments there is a flask command that gives system administrators
the ability to load the data from a csv file directly into the database.

**Warning** This process is not very robust at this point and there is
risk of leaving the database in an inconsistent state. It is strongly
recommended to back up the database before starting this operation and
to run the command on a development server first and see if the results
are as expected.

Preparation steps
-----------------
-  Create department if it does not exist
-  Add ranks in hierarchical order, make sure all the ranks present in
   the csv are added

Layout of the csv file
----------------------
The csv file can have the following fields:
```
 department_id
 unique_internal_identifier
 first_name
 last_name
 middle_initial
 suffix
 gender
 race
 employment_date
 birth_year
 star_no
 job_title
 unit_id
 start_date
 resign_date
 salary
 salary_year
 salary_is_fiscal_year
 overtime_pay
```


Explanation of the individual fields
------------------------------------
General information:
- `department_id` - ID of department in the server database, for example `1` for Chicago Police Department can be found in
   url for that department: `https://openoversight.com/departments/1`.
- `unique_internal_identifier` - A string or number that can be used to uniquely identify the officer, in departments in
   which the badge number stays with the officer using that number is fine, otherwise it is recommended to leave this
   blank and provide the `star_no` instead.
- `first_name` & `last_name` & `middle_initial`
- `suffix` - One of the following values: `Jr, Sr, II, III, IV, V`.
- `gender` - One of the following values: `M`, `F`, `Other` or `Not Sure`.
- `race` - One of the following values: `BLACK`, `WHITE`, `ASIAN`, `HISPANIC`, `NATIVE AMERICAN`, `PACIFIC ISLANDER`, `Other`, `Not Sure`.
- `employment_date` - Start of employment with this department.
- `birth_year` - Integer representing the birth year of the officer in a `yyyy` format

Current Employment information:
- `star_no` - Star or badge number, might be related to current rank.
- `job_title` - Rank or title, needs to be added to this department verbatim or `Not Sure`,
- `unit_id` - ID of unit within the department.
- `start_date` - Start date of this assignment.
- `resign_date` - Resignation date of this assignment.

Salary information:
- `salary_year` - Year of which the salary information is provided in a `yyyy` format.
- `salary_is_fiscal_year` - `true` or `false`, salary information is on fiscal year basis vs. calendar year.
- `salary` - Salary in given year.
- `overtime_pay` - Overtime received in given year.

Required fields
- `department_id`, `first_name`, `last_name`, `job_title` and either `star_no` or `unique_internal_identifier` are required.
- `employment_date`, `start_date` and `resign_date` can be either in `yyyy-mm-dd` or `mm/dd/yyyy` format - if the column is present
   the field cannot be left blank.

Command-line options
- `--no-create` - For each line in the CSV, update an existing officer if one exists, but do not create any new officers. If an officer in the CSV is not already in OpenOversight, the line will be ignored.
- `--update-by-name` - Update officers by `first_name` and `last_name`. Useful when `unique_internal_identifier` and `star_no` are not available.
- `--update-static-fields` - Allow modifications to normally-static fields like `race`, `birth_year`, etc., which OpenOversight normally prevents from being modified. Values in the database will be overwritten with values in the CSV.

The command to run on the server
--------------------------------
`/usr/src/app/OpenOversight$ flask bulk-add-officers [/path/to/csv_file.csv]`
