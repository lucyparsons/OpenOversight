delete from officers.assignments;
drop table joined_offid;

create temp table joined_offid AS
(select officer_id, t2."STAR1", t2."STAR2", t2."STAR3", 
t2."STAR4", t2."STAR5", t2."STAR6", t2."STAR7", t2."STAR8", 
t2."STAR9", t2."STAR10", t2."CPD_UNIT_ASSIGNED_NO",
t2."EFFECTIVE_DATE", t2."END_DATE", t3."DESCR"
from officers.roster t1
inner join public.assignments t2
on t2."LAST_NME" = t1.last_name
and t2."FIRST_NME" = t1.first_name
inner join public.invisinst t3
on t3."LAST_NME" = t1.last_name
and t3."FIRST_NME" = t1.first_name
);

insert into officers.assignments
	(officer_id, star_no, unit, start_date, resign_date, rank)
select 
    officer_id, 
    star_no, 
    unit, 
    start_date, 
    resign_date,
    rank from 
    (select officer_id,
       unnest(array["STAR1", "STAR2", "STAR3", 
              "STAR4", "STAR5", "STAR6", "STAR7", "STAR8", 
              "STAR9", "STAR10"]) as star_no,
       "EFFECTIVE_DATE" as start_date,
       "END_DATE" as resign_date,
       "CPD_UNIT_ASSIGNED_NO" as unit,
       "DESCR" as rank
       from joined_offid) foo 
where foo.star_no is not null;