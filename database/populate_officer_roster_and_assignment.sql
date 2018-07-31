delete from public.officers;
delete from public.assignments;

-- populate chicago police department officers cpd corresponds to pd_id=1
insert into public.officers
    (last_name, first_name, middle_initial, suffix, race, gender, employment_date, pd_id)
select
    "Last Name",
    "First Name",
    "Middle Initial",
    "Suffix",
    "Race",
    "Gender",
    "Date of Employment",
    1
from public.base_roster;

-- put star numbers, ranks in assignments table
insert into public.assignments
    (officer_id, star_no, rank)
select t1.id as officer_id, cast(t2."Star No." as integer) as star_no, t2."Current Rank" as rank
    from public.officers t1
    inner join public.base_roster t2
          on t1.last_name = t2."Last Name" and t1.first_name = t2."First Name" 
          and t1.race = t2."Race" and t1.gender = t2."Gender"
          and t1.employment_date = t2."Date of Employment";

-- fill in officers table with age if we have it from invisible institute
-- got ~90% matches here

UPDATE officers
SET birth_year = foo.birth_year
FROM
 (select t1."DOBYEAR" as birth_year, t2.id as officer_id
from public.invisinst t1
 join public.officers t2
on t1."FIRST_NME" = t2.first_name and t1."LAST_NME" = t2.last_name
and t1."SEX_CODE_CD" = t2.gender and t1."RACE" = t2.race
and t1."MIDDLE_INITIAL" = t2.middle_initial) foo
WHERE
 foo.officer_id = officers.id;
