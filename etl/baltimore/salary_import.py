# match first name and hire date
# if multiple matches, match (first letter of) middle initial
# if multiple matches, match last name
    # if no matches, print all matched so far and throw warning/error
    # if multiple matches, match suffix (from list of possible suffixes)
        # if no matches, print all matched so far and throw warning/error

import pandas as pd
import os
import sys
import glob
import re
import numpy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from OpenOversight.app import create_app, models  # noqa E402
from OpenOversight.app.models import db  # noqa E402

app = create_app('development')
db.app = app

name_re = re.compile(r'^(?P<last_name>[a-zA-Z- \'\.]+?)(?:[ ,](?P<suffix>Jr|jr|Sr|sr|II|ii|2nd|III|iii|3rd|IV|iv)\.?)?,(?P<first_name>[a-zA-Z- \'\.]+?)(?: (?P<middle_initial>[A-Z])\.?)?$')

NAME_COL = 0
AGENCY_ID_COL = 2
HIRE_DATE_COL = 4
SALARY_COL = 5
TOTAL_PAY_COL = 6


def add_salary(officer, matches, year):
    row = matches.loc[matches.first_valid_index()]

    if type(row[SALARY_COL]) == str:
        annual_salary = float(row[SALARY_COL].replace('$', ''))
    elif type(row[SALARY_COL]) == float or type(row[SALARY_COL]) == numpy.float64:
        annual_salary = row[SALARY_COL]
    else:
        raise Exception(type(row[SALARY_COL]))

    if type(row[TOTAL_PAY_COL]) == str:
        overtime_pay = float(row[TOTAL_PAY_COL].replace('$', '')) - annual_salary
    elif type(row[TOTAL_PAY_COL]) == float or type(row[TOTAL_PAY_COL]) == numpy.float64:
        if numpy.isnan(row[TOTAL_PAY_COL]):
            overtime_pay = 0
        else:
            overtime_pay = row[TOTAL_PAY_COL] - annual_salary

    salary = models.Salary(
        officer_id=officer.id,
        salary=annual_salary,
        overtime_pay=overtime_pay or None,
        year=year,
        is_fiscal_year=True
    )
    db.session.add(salary)


def import_salaries(directory):
    salary_sets = {}
    for csvfile in glob.glob(directory + '/*.csv'):
        year = int(re.search(r'20\d\d', csvfile)[0])
        # read in CSV, parse out parts of name
        df = pd.read_csv(csvfile)
        # # Only want A99 department IDs
        df = df[df.iloc[:,AGENCY_ID_COL].str.startswith('A99')]
        # Skip officers with redacted names
        df = df[~df.iloc[:,NAME_COL].str.startswith('BPD ')]
        # Split name into multiple columns
        df = df.join(df.iloc[:,0].str.extract(name_re))
        # Normalize suffixes
        df = df.replace('jr', 'Jr').replace('sr', 'Sr')\
            .replace('2nd', 'II').replace('3rd', 'III')\
            .replace('ii', 'II').replace('iii', 'III').replace('iv', 'IV')

        salary_sets[year] = df

    # foreach officer in DB, go matching
    officers = models.Officer.query.all()
    for officer in officers:
        print(officer.unique_internal_identifier)
        hire_date = officer.employment_date.strftime('%m/%d/%Y')
        for year, df in salary_sets.items():
            # print(year)
            # Match on first name, last name, hire date
            matches = df[df['first_name'].str.match(officer.first_name)]\
                [lambda df: df['last_name'].str.match(officer.last_name)]\
                [lambda df: df.iloc[:,HIRE_DATE_COL].str.startswith(hire_date)]
            if matches.empty:
                continue
            elif len(matches) == 1:
                add_salary(officer, matches, year)
            elif len(matches) > 1:
                # Match on middle initial
                matches = matches[matches['middle_initial'].str.match(officer.middle_initial)]
                if matches.empty:
                    raise Exception(
                        'Could not match on middle name for {} {} {}'.format(
                            officer.first_name, officer.middle_initial, officer.last_name))
                elif len(matches) == 1:
                    add_salary(officer, matches, year)
                elif len(matches) > 1:
                    # Match on suffix
                    matches = matches[matches['suffix'].str.match(officer.suffix)]
                    if len(matches) == 1:
                        add_salary(officer, matches, year)
                    else:
                        raise Exception(
                            'Could not match on suffix for {} {} {} {}'.format(
                                officer.first_name, officer.middle_initial,
                                officer.last_name, officer.suffix))

    db.session.commit()


if __name__ == '__main__':
    import_salaries(sys.argv[1])
