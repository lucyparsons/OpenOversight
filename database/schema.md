<!--

classDiagram
class users{
 *INTEGER id NOT NULL
   VARCHAR<36> _uuid NOT NULL
   INTEGER ac_department_id
   TIMESTAMP approved_at
   INTEGER approved_by
   TIMESTAMP confirmed_at
   INTEGER confirmed_by
   TIMESTAMP created_at NOT NULL
   INTEGER dept_pref
   TIMESTAMP disabled_at
   INTEGER disabled_by
   VARCHAR<64> email
   BOOLEAN is_administrator
   BOOLEAN is_area_coordinator
   TIMESTAMP last_confirmation_sent_at
   TIMESTAMP last_reset_sent_at
   VARCHAR<128> password_hash
   VARCHAR<64> username
}
class departments{
 *INTEGER id NOT NULL
   TIMESTAMP created_at NOT NULL
   INTEGER created_by
   TIMESTAMP last_updated_at NOT NULL
   INTEGER last_updated_by
   VARCHAR<255> name NOT NULL
   VARCHAR<100> short_name NOT NULL
   VARCHAR<2> state NOT NULL
   VARCHAR<100> unique_internal_identifier_label
}
class jobs{
 *INTEGER id NOT NULL
   TIMESTAMP created_at NOT NULL
   INTEGER created_by
   INTEGER department_id
   BOOLEAN is_sworn_officer
   VARCHAR<255> job_title NOT NULL
   TIMESTAMP last_updated_at NOT NULL
   INTEGER last_updated_by
   INTEGER order NOT NULL
}
class officers{
 *INTEGER id NOT NULL
   INTEGER birth_year
   TIMESTAMP created_at NOT NULL
   INTEGER created_by
   INTEGER department_id
   DATE employment_date
   VARCHAR<120> first_name
   VARCHAR<5> gender
   VARCHAR<120> last_name
   TIMESTAMP last_updated_at NOT NULL
   INTEGER last_updated_by
   VARCHAR<120> middle_initial
   VARCHAR<120> race
   VARCHAR<120> suffix
   VARCHAR<50> unique_internal_identifier
}
class unit_types{
 *INTEGER id NOT NULL
   TIMESTAMP created_at NOT NULL
   INTEGER created_by
   INTEGER department_id
   VARCHAR<120> description
   TIMESTAMP last_updated_at NOT NULL
   INTEGER last_updated_by
}
class raw_images{
 *INTEGER id NOT NULL
   BOOLEAN contains_cops
   TIMESTAMP created_at NOT NULL
   INTEGER created_by
   INTEGER department_id
   VARCHAR<255> filepath
   VARCHAR<120> hash_img
   BOOLEAN is_tagged
   TIMESTAMP last_updated_at NOT NULL
   INTEGER last_updated_by
   TIMESTAMP taken_at
}
class locations{
 *INTEGER id NOT NULL
   VARCHAR<100> city
   TIMESTAMP created_at NOT NULL
   INTEGER created_by
   VARCHAR<100> cross_street1
   VARCHAR<100> cross_street2
   TIMESTAMP last_updated_at NOT NULL
   INTEGER last_updated_by
   VARCHAR<2> state
   VARCHAR<100> street_name
   VARCHAR<5> zip_code
}
class license_plates{
 *INTEGER id NOT NULL
   TIMESTAMP created_at NOT NULL
   INTEGER created_by
   TIMESTAMP last_updated_at NOT NULL
   INTEGER last_updated_by
   VARCHAR<8> number NOT NULL
   VARCHAR<2> state
}
class links{
 *INTEGER id NOT NULL
   VARCHAR<255> author
   TIMESTAMP created_at NOT NULL
   INTEGER created_by
   TEXT description
   BOOLEAN has_content_warning NOT NULL
   TIMESTAMP last_updated_at NOT NULL
   INTEGER last_updated_by
   VARCHAR<100> link_type
   VARCHAR<100> title
   TEXT url NOT NULL
}
class officer_links{
 *INTEGER link_id NOT NULL
   *INTEGER officer_id NOT NULL
   TIMESTAMP created_at NOT NULL
}
class notes{
 *INTEGER id NOT NULL
   TIMESTAMP created_at NOT NULL
   INTEGER created_by
   TIMESTAMP last_updated_at NOT NULL
   INTEGER last_updated_by
   INTEGER officer_id
   TEXT text_contents
}
class descriptions{
 *INTEGER id NOT NULL
   TIMESTAMP created_at NOT NULL
   INTEGER created_by
   TIMESTAMP last_updated_at NOT NULL
   INTEGER last_updated_by
   INTEGER officer_id
   TEXT text_contents
}
class salaries{
 *INTEGER id NOT NULL
   TIMESTAMP created_at NOT NULL
   INTEGER created_by
   BOOLEAN is_fiscal_year NOT NULL
   TIMESTAMP last_updated_at NOT NULL
   INTEGER last_updated_by
   INTEGER officer_id
   DOUBLE_PRECISION overtime_pay
   DOUBLE_PRECISION salary NOT NULL
   INTEGER year NOT NULL
}
class assignments{
 *INTEGER id NOT NULL
   TIMESTAMP created_at NOT NULL
   INTEGER created_by
   INTEGER job_id NOT NULL
   TIMESTAMP last_updated_at NOT NULL
   INTEGER last_updated_by
   INTEGER officer_id
   DATE resign_date
   VARCHAR<120> star_no
   DATE start_date
   INTEGER unit_id
}
class faces{
 *INTEGER id NOT NULL
   TIMESTAMP created_at NOT NULL
   INTEGER created_by
   INTEGER face_height
   INTEGER face_position_x
   INTEGER face_position_y
   INTEGER face_width
   BOOLEAN featured NOT NULL
   INTEGER img_id
   TIMESTAMP last_updated_at NOT NULL
   INTEGER last_updated_by
   INTEGER officer_id
   INTEGER original_image_id
}
class incidents{
 *INTEGER id NOT NULL
   INTEGER address_id
   TIMESTAMP created_at NOT NULL
   INTEGER created_by
   DATE date
   INTEGER department_id
   TEXT description
   TIMESTAMP last_updated_at NOT NULL
   INTEGER last_updated_by
   VARCHAR<50> report_number
   TIME time
}
class officer_incidents{
 *INTEGER incident_id NOT NULL
   *INTEGER officer_id NOT NULL
   TIMESTAMP created_at NOT NULL
}
class incident_links{
 *INTEGER incident_id NOT NULL
   *INTEGER link_id NOT NULL
   TIMESTAMP created_at NOT NULL
}
class incident_license_plates{
 *INTEGER incident_id NOT NULL
   *INTEGER license_plate_id NOT NULL
   TIMESTAMP created_at NOT NULL
}
class incident_officers{
 *INTEGER incident_id NOT NULL
   *INTEGER officers_id NOT NULL
   TIMESTAMP created_at NOT NULL
}
users "0..1" -- "0..n" users
users "0..1" -- "0..n" users
departments "0..1" -- "0..n" users
departments "0..1" -- "0..n" users
users "0..1" -- "0..n" users
users "0..1" -- "0..n" departments
users "0..1" -- "0..n" departments
departments "0..1" -- "0..n" jobs
users "0..1" -- "0..n" jobs
users "0..1" -- "0..n" jobs
users "0..1" -- "0..n" officers
users "0..1" -- "0..n" officers
departments "0..1" -- "0..n" officers
departments "0..1" -- "0..n" unit_types
users "0..1" -- "0..n" unit_types
users "0..1" -- "0..n" unit_types
users "0..1" -- "0..n" raw_images
users "0..1" -- "0..n" raw_images
departments "0..1" -- "0..n" raw_images
users "0..1" -- "0..n" locations
users "0..1" -- "0..n" locations
users "0..1" -- "0..n" license_plates
users "0..1" -- "0..n" license_plates
users "0..1" -- "0..n" links
users "0..1" -- "0..n" links
officers "1" -- "0..n" officer_links
links "1" -- "0..n" officer_links
users "0..1" -- "0..n" notes
officers "0..1" -- "0..n" notes
users "0..1" -- "0..n" notes
users "0..1" -- "0..n" descriptions
officers "0..1" -- "0..n" descriptions
users "0..1" -- "0..n" descriptions
users "0..1" -- "0..n" salaries
users "0..1" -- "0..n" salaries
officers "0..1" -- "0..n" salaries
users "0..1" -- "0..n" assignments
users "0..1" -- "0..n" assignments
unit_types "0..1" -- "0..n" assignments
officers "0..1" -- "0..n" assignments
jobs "1" -- "0..n" assignments
raw_images "0..1" -- "0..n" faces
users "0..1" -- "0..n" faces
raw_images "0..1" -- "0..n" faces
users "0..1" -- "0..n" faces
officers "0..1" -- "0..n" faces
users "0..1" -- "0..n" incidents
departments "0..1" -- "0..n" incidents
locations "0..1" -- "0..n" incidents
users "0..1" -- "0..n" incidents
incidents "1" -- "0..n" officer_incidents
officers "1" -- "0..n" officer_incidents
incidents "1" -- "0..n" incident_links
links "1" -- "0..n" incident_links
incidents "1" -- "0..n" incident_license_plates
license_plates "1" -- "0..n" incident_license_plates
incidents "1" -- "0..n" incident_officers
officers "1" -- "0..n" incident_officers

-->
