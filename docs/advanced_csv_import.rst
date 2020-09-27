Advanced csv import
=============================================

This is the documentation of the advanced csv import command ``advanced_csv_import``. For the documentation of the less complicated
bulk-upload command ``bulk-add-officers`` see :doc:`bulk_upload`. ``bulk-add-officers`` accepts one csv containing information
about the officer, including badge-number, jobs and salary and makes decisions on whether to update rows in the database
or create new entries based on the existing data.

The advanced csv upload is for the most part a way to copy data for one department into the database with as little as possible logic added on.
So the tables provided in csv form represent the data that will be inside the sql tables after running the command.
(With a few exceptions for many-to-many relationships and auxiliary models like location and license plates)

Before you start
----------------

CSV uploads should always be tested locally or in other non-production environments and it is strongly recommended
to have the database backed up before running the command. The command is designed to fail early and will
only commit the changes if it didn't encounter any problems. The command however is pretty powerful
and can therefore lead to data loss and inconsistencies if the provided csv files are not prepared correctly.

Explanation of the command
--------------------------

::

  /usr/src/app/OpenOversight$ flask advanced-csv-import --help
  Usage: flask advanced-csv-import [OPTIONS] DEPARTMENT_NAME

  Add or update officers, assignments, salaries, links and incidents from
  csv files in the department DEPARTMENT_NAME.

  The csv files are treated as the source of truth. Existing entries might
  be overwritten as a result, backing up the database and running the
  command locally first is highly recommended.

  See the documentation before running the command.

  Options:
  --officers-csv PATH
  --assignments-csv PATH
  --salaries-csv PATH
  --links-csv PATH
  --incidents-csv PATH
  --force-create          Only for development/testing!
  --help                  Show this message and exit.


The command expects one mandatory argument the department name.
This is to reduce the chance of making changes to the wrong department by mixing up files.
Then there are 5 options to include paths to officers, assignments, salaries, incidents and links csv files.
Finally there is a ``--force-create`` flag that allows to delete and overwrite existing entries in the database.
This is only supposed to be used in non-production environments and to allow replication of the data of another (in most cases production)
instance to local environments to test the import command locally first. More details on that flag at the end of the document: :ref:`ref-aci-force-create`.

General overview of the csv import:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following lists the header fields that each csv can contain. If the csv includes any other fields, the command will fail.
However the fields are not case-sensitive and spaces are treated as ``_``. So ``Officer ID`` can be used instead of ``officer_id``.

*All optional fields can be left blank and will be inserted as* ``NULL`` *or empty string as appropriate.*
**Warning:** When updating a record a field that is left blank might overwrite an existing record.
This can only be prevented by not including the column in the csv at all.

.. _ref-aci-formats:

Formats
~~~~~~~~~~~~
- date: The date should be provided in ``YYYY-MM-DD`` format.
- time: Time should be provided in ``HH:MM:SS`` 24h-format in the respective timezone.


The ``id`` field
~~~~~~~~~~~~~~~~~

Each csv corresponds to a table in the OpenOversight database. And each csv file has to include ``id`` as a field in the table.
That field has one primary purpose: If the field is blank, it is assumed that that row is a new entry.
If the field contains a number however, it is assumed that a record with that particular id already exists in the database
and the record will be updated according to the provided fields. Finally in the case of officers and incidents
there is a third option where the ``id`` field can contain a string that starts with ``#``. This also indicates a new record,
but that new record can be referenced in other provided tables. (for example as the ``officer_id`` in the salaries csv)



Officers csv
^^^^^^^^^^^^
- Required: ``id, department_name``
- Optional: ``last_name, first_name, middle_initial, suffix, race, gender, employment_date, birth_year, unique_internal_identifier``
- Ignored: ``badge_number, job_title, most_recent_salary`` (Unused but command will not fail when field is present)

Details:
~~~~~~~~
-  ``department_name`` Name of department exactly as in the server database.
   This needs to match the department name provided with the command.
-  ``unique_internal_identifier`` A string or number that can be used to
   uniquely identify the officer, in departments in which the badge
   number stays with the officer using that number is fine. Can and should be left blank
   if no such number is available.
-  ``first_name`` & ``last_name`` Will be inserted into the database as is.
-  ``middle_initial`` Usually up to one character, but can be more.
-  ``suffix`` Choice of ``Jr, Sr, II, III, IV, V``.
-  ``gender`` Choice of ``M``, ``F``, ``Other``.
-  ``race`` One of ``BLACK``, ``WHITE``, ``ASIAN``, ``HISPANIC``, ``NATIVE AMERICAN``, ``PACIFIC ISLANDER``, ``Other``.
-  ``employment_date`` :ref:`Date <ref-aci-formats>` representing the start of employment with this department.
-  ``birth_year`` Integer representing the birth year of the officer.

Assignments csv
^^^^^^^^^^^^^^^
- Required: ``id, officer_id, job_title``
- Optional: ``badge_number, unit_id, start_date, resign_date``

Details:
~~~~~~~~
-  ``officer_id`` Number referring to ``id`` of existing officer or string starting with ``#`` referring to a newly created officer in the provided officers csv.
-  ``badge_number`` Any string that represents the star or badge number of the officer. In some departments this number changes with the assignment.
-  ``job_title`` The job title, needs to be created for that department.
-  ``unit_id`` Id of existing unit within the department.
-  ``start_date`` Start :ref:`date <ref-aci-formats>` of this assignment.
-  ``resign_date`` End :ref:`date <ref-aci-formats>` of this assignment.

Salaries csv
^^^^^^^^^^^^
- Required: ``id, officer_id, salary, year``
- Optional: ``overtime_pay, is_fiscal_year``

Details:
~~~~~~~~
-  ``officer_id`` Integer referring to ``id`` of existing officer or string starting with ``#`` referring to a newly created officer in the provided officers csv
- ``salary`` Number representing the officer's salary in the given year.
- ``year`` Integer, the year this salary information refers to.
- ``overtime_pay`` Number representing the amount of overtime payment for offer in given year.
- ``is_fiscal_year`` Boolean value, indicating whether the provided year refers to calendar year or fiscal year.
  The values ``true``, ``t``, ``yes`` and  ``y`` are treated as "yes, the salary is for the fiscal year", all others (including blank) as "no"

Incidents csv
^^^^^^^^^^^^^
- Required: ``id, department_name``
- Optional: ``date, time, report_number, description, street_name, cross_street1, cross_street2, city, state, zip_code,
  creator_id, last_updated_id, officer_ids, license_plates``

Details:
~~~~~~~~
-  ``department_name`` Name of department exactly as in the server database.
   This needs to match the department name provided with the command.
- ``date`` :ref:`Date <ref-aci-formats>` of the incident
- ``time`` :ref:`Time <ref-aci-formats>` of the incident
- ``report_number`` String representing any kind of number assigned to complaints or incidents by the police department.
- ``description`` Text description of the incident.
- ``street_name`` Name of the street the incident occurred, but should not include the street number.
- ``cross_street1``, ``cross_street2`` The two closest intersecting streets.
- ``city``, ``state``, ``zip_code`` State needs to be in 2 letter abbreviated notation.
- ``creator_id``, ``last_updated_id`` Id of existing user shown as responsible for adding this entry.
- ``officer_ids`` Ids of officers involved in the incident, separated by ``|``.
  
  - Each individual id can either be an integer referring to an existing officer or a string starting with ``#`` referring to a newly created officer.
  - Example: ``123|#C1|1627`` for three officers, one with id 123, one with 1627 and one whose record was created in the officers csv
    and whose id-field was the string ``#C1``.

- ``license_plates`` all license plates involved in the incident. If there is more than one, they can be separated with a ``|``.
  
  - Each license plate consists of the license plate number and optionally a state in abbreviated form separated by an underscore ``_``.
  - Example: ``ABC123_IL|B991`` for one license plate with number ``ABC123`` from Illinois and one with number ``B991`` and no associated state.


Links csv
^^^^^^^^^
- Required: ``id, url``
- Optional: ``title, link_type, description, author, creator_id, officer_ids, incident_ids``

Details:
~~~~~~~~
- ``url`` Full url of the link starting with ``http://`` or ``https://``.
- ``title`` Text that will be displayed as the link.
- ``description`` A short description of the link.
- ``link_type`` Choice of ``Link``, ``YouTube Video`` and ``Other Video``.
- ``author`` The source or author of the linked article, report, video.
- ``creator_id`` Id of existing user shown as responsible for adding this entry.
- ``officer_ids`` Ids of officer profiles this link should be visible on, separated by ``|``. See same field in incidents above for more details.
- ``incidents_ids`` Ids of incidents this link should be associated with, separated by ``|``. Just like ``officer_ids`` this can contain strings
  starting with ``#`` to refer to an incident created in the incident csv.

Examples
---------
Example csvs can be found in the repository under ``OpenOversight/tests/test_csvs``.

.. _ref-aci-force-create:

Local development flag ``--force-create``
-----------------------------------------

This flag chances the behavior when an integer is provided as ``id``. Instead of updating an existing record,
a new record will be created and assigned the given ``id``. If a record with that ``id`` already exists in the
database, it will be deleted before the new record is created.

This functionality is intended to be used to import csv files downloaded from `OpenOversight download page </download/all>`_
to get a local copy of the production data for one department in the local development database.
