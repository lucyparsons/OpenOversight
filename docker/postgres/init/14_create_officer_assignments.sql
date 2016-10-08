drop table if exists officers.assignments;

create table officers.assignments (
        assignment_id serial primary key,
        officer_id integer references officers.roster (officer_id),
        star_no integer,
        rank varchar(100),
        unit integer,
        start_date date,
        resign_date date
);