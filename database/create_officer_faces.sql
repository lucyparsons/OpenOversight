drop table if exists officers.faces;

create table officers.faces (
        img_id serial primary key,
        img_path varchar(200),
        officer_id integer references officers.roster (officer_id),
        face_position box
);