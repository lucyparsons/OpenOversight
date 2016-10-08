drop table if exists officers.raw_images;

create table officers.raw_images (
        img_id serial primary key,
        filepath varchar(100),
        hash_img varchar(100),
        is_tagged boolean
);