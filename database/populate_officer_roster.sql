delete from officers.roster;

-- we have several sources of data, use ii first
insert into officers.roster
	(last_name, first_name, race, gender, employment_date, birth_year)
select
    "LAST_NME",
    "FIRST_NME",
    "RACE",
    "SEX_CODE_CD",
    officers.to_date(lpad("APPOINTED_DATE", 9, '0')),
    "DOBYEAR"
from public.invisinst;

-- merge in rows from more recent roster from foia
-- recent foia data does not have birth year
insert into officers.roster
    (last_name, first_name, middle_initial, race, gender, employment_date)
select
    "Last Name",
    "First Name",
    "Middle Initial",
    "Race",
    "Gender",
    "Date of Employment"
from public.roster
where
    not exists (
        select last_name, first_name from officers.roster
        where officers.roster.last_name = public.roster."Last Name"
        and officers.roster.first_name = public.roster."First Name"
    );