import pandas as pd
import os
import sys
import csv
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from OpenOversight.app import create_app, models  # noqa E402
from OpenOversight.app.models import db  # noqa E402

app = create_app('development')
db.app = app

fieldnames = [
    'department_id',
    'unique_internal_identifier',
    'first_name',
    'last_name',
    'middle_initial',
    'suffix',
    'gender',
    'race',
    'employment_date',
    'birth_year',
    'star_no',
    'rank',
    'unit',
    'star_date',
    'resign_date'
]

columns = {
    # 'Location': 'location',
    'EMPLID': 'employee_id',
    'Last Name': 'last_name',
    'First Name': 'first_name',
    'Middle Name': 'middle_initial',
    'SEX': 'sex',
    'Ethnic Group': 'ethnic_group',
    'Service Date': 'service_date',
    'Rehire Date': 'rehire_date',
    'Promotion Date': 'promotion_date',
    'Job Code': 'job_code',
    'Job Title': 'job_title',
    'Supv ID': 'supervisor_employee_id',
    # 'In Lieu': 'in_lieu',
    'Position Number': 'position_number',
    'Grade': 'grade',
    'GL Pay Type': 'gl_pay_type',
    # 'Locatlity': 'locality', # sic
    'SEQ# (A99 only)': 'seq_no'
    # 'SEQ#': 'seq_no'
}


def load(filename):
    print("Importing raw roster", filename)
    df = pd.read_excel(filename)
    for column in columns.keys():
        try:
            assert column in df.columns
        except AssertionError:
            print('Did not find column {} in roster'.format(column))
            raise
    df.rename(columns=columns, inplace=True)
    try:
        df.to_sql('roster_raw', db.engine)
    except ValueError:
        print('Raw roster already imported')
    else:
        print('Raw roster successfully imported')

    departments = models.Department.query.all()
    bpd = None
    for department in departments:
        if department.name == 'Baltimore City Police Department':
            print('Department already created')
            bpd = department
    if not bpd:
        print("Creating department")
        bpd = models.Department(name='Baltimore City Police Department',
                                short_name='BPD')
        db.session.add(bpd)
        db.session.commit()

    with open('export.csv', 'w', newline='') as csvf:
        writer = csv.DictWriter(csvf, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for pig in df.itertuples():
            print(pig.seq_no)
            assignment_date = None
            if pig.promotion_date and pig.promotion_date != ' ' and type(pig.promotion_date) != float:
                if type(pig.promotion_date) == str:
                    assignment_date = datetime.strptime(pig.promotion_date, '%m/%d/%Y').date()
                else:
                    assignment_date = pig.promotion_date.date()
            elif pig.rehire_date and pig.rehire_date != ' ' and type(pig.rehire_date) != float:
                if type(pig.rehire_date) == str:
                    assignment_date = datetime.strptime(pig.rehire_date, '%m/%d/%Y').date()
                else:
                    assignment_date = pig.rehire_date.date()

            if pig.service_date and pig.service_date != ' ' and type(pig.service_date) != float:
                if type(pig.service_date) == str:
                    employment_date = datetime.strptime(pig.service_date, '%m/%d/%Y').date()
                else:
                    employment_date = pig.service_date.date()
                if not assignment_date:
                    assignment_date = employment_date

            try:
                rint = int(pig.ethnic_group)
            except ValueError:
                race = pig.ethnic_group
            else:
                if rint == 1:
                    race = 'White'
                elif rint == 2:
                    race = 'Black or African American'
                elif rint == 3:
                    race = 'Hispanic'
                elif rint == 4:
                    race = 'Asian/Pacific Islander'
                elif rint == 5:
                    race = 'American Indian/Alaska Native'
                elif rint == 6:
                    race = 'Not Applicable (Non-U.S.)'
                elif rint == 7:
                    race = 'Not Specified'

            writer.writerow({
                'department_id': bpd.id,
                'unique_internal_identifier': pig.seq_no,
                'first_name': pig.first_name,
                'middle_initial': pig.middle_initial if type(pig.middle_initial) == str else None,
                'last_name': pig.last_name,
                'gender': pig.sex,
                'race': race,
                'employment_date': employment_date,
                'rank': pig.job_title,
                'star_date': assignment_date
            })

    print("Finished data import!")


if __name__ == '__main__':
    load(sys.argv[1])
