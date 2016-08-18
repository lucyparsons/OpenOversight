insert into officers.roster
    (last_name, first_name, middle_initial, race, gender, employment_date)
select
    "Last Name",
    "First Name",
    "Middle Initial",
    "Race",
    "Gender",
    "Date of Employment"
from public.roster;