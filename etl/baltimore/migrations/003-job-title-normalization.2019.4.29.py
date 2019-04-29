import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from OpenOversight.app import create_app, models  # noqa E402
from OpenOversight.app.models import db  # noqa E402

app = create_app('development')
db.app = app

if __name__ == '__main__':
    # Load code/title CSVs
    jobs = {}
    for filename in ['scraped_job_codes.csv', 'additional_job_codes.csv']:
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                jobs[int(row['Job Code'])] = row['Job Title']

    # Load rosters
    seq_code_title = {}
    rosters = [
        'Active_employees_as_of_May_3_2018.csv',
        'Employee_Information_for_Release.csv'
    ]
    for roster in rosters:
        with open(roster, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                seq = row.get('SEQ# (A99 only)')
                if not seq:
                    seq = row.get('SEQ#')
                if seq not in seq_code_title:
                    seq_code_title[seq] = {}
                seq_code_title[seq][row['Job Title']] = int(row['Job Code'])

    # Normalize job titles in DB
    for officer in models.Officer.query.all():
        for assignment in officer.assignments:
            code = seq_code_title[officer.unique_internal_identifier][assignment.rank]
            assignment.rank = jobs[code].replace(' - EID','')  # No need to keep the EID distinction in BPD Watch
            db.session.add(assignment)
    db.session.commit()
