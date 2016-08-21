DROP SCHEMA IF EXISTS officers CASCADE;
CREATE SCHEMA officers;

-- stored procedure to handle 2 digit dates ugh
CREATE OR REPLACE FUNCTION officers.to_date(text)
  RETURNS date AS
$BODY$
SELECT CASE WHEN right($1, 2) > '30' THEN
         to_date(left($1, 7) || '19' || right($1, 2), 'DD-MON-YYYY')
      ELSE
         to_date(left($1, 7) || '20' || right($1, 2), 'DD-MON-YYYY')
      END
$BODY$
  LANGUAGE sql IMMUTABLE;