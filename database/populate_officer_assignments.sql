delete from officers.assignments;
drop table joined_offid;

create temp table joined_offid AS
select officer_id, "STAR1", "STAR2", "STAR3", 
"STAR4", "STAR5", "STAR6", "STAR7", "STAR8", 
"STAR9", "STAR10", "CPD_UNIT_ASSIGNED_NO",
"EFFECTIVE_DATE", "END_DATE"
from public.assignments
inner join officers.roster 
on public.assignments."LAST_NME" = officers.roster.last_name
and public.assignments."FIRST_NME" = officers.roster.first_name;

select officer_id, star_no, unit, start_date, resign_date from 
    (select officer_id,
       unnest(array["STAR1", "STAR2", "STAR3", 
              "STAR4", "STAR5", "STAR6", "STAR7", "STAR8", 
              "STAR9", "STAR10"]) as star_no,
       "EFFECTIVE_DATE" as start_date,
       "END_DATE" as resign_date,
       "CPD_UNIT_ASSIGNED_NO" as unit
       from joined_offid) foo 
    where foo.star_no is not null;

insert into officers.assignments
	(officer_id, star_no, unit, start_date, resign_date)
select 
    officer_id, 
    star_no, 
    unit, 
    start_date, 
    resign_date from 
    (select officer_id,
       unnest(array["STAR1", "STAR2", "STAR3", 
              "STAR4", "STAR5", "STAR6", "STAR7", "STAR8", 
              "STAR9", "STAR10"]) as star_no,
       "EFFECTIVE_DATE" as start_date,
       "END_DATE" as resign_date,
       "CPD_UNIT_ASSIGNED_NO" as unit
       from joined_offid) foo 
where foo.star_no is not null;