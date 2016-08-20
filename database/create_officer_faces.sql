drop table if exists officers.faces;

create table officers.faces (
        tag_id serial primary key,
        img_id integer references officers.raw_images (img_id),
        officer_id integer references officers.roster (officer_id),
        face_position box
);