delete from officers.unit_types;

insert into officers.unit_types
	(unit, descrip)
select distinct on ("CPD_UNIT_ASSIGNED_NO")
    "CPD_UNIT_ASSIGNED_NO", 
    "UNITDESCR"
from public.invisinst
where
    "CPD_UNIT_ASSIGNED_NO" is not null;