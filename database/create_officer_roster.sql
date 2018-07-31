drop table if exists officers.roster;

create table officers.roster (
        officer_id serial primary key,
        last_name varchar(80),
        first_name varchar(80),
        middle_initial varchar(10),
        suffix varchar(10),
        race varchar(40),
        gender varchar(40),
        employment_date date,
        birth_year integer
);
