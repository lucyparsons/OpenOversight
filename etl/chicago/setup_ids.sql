-- use new unique id for openoversight
ALTER TABLE roster RENAME index TO oo_id;

-- set openoversight id as primary key
ALTER TABLE roster ADD PRIMARY KEY (oo_id);
