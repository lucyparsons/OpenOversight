import pandas as pd
from sqlalchemy import create_engine

import dbcred


def load(filename):
    df = pd.read_excel(filename)

    expected_columns = ['LAST_NME', 'FIRST_NME',
                        'SEX_CODE_CD', 'RACE', 'CURRAGE',
                        'APPOINTED_DATE', 'EFFECTIVE_DATE',
                        'END_DATE', 'CPD_UNIT_ASSIGNED_NO', 'STAR1',
                        'STAR2', 'STAR3', 'STAR4', 'STAR5',
                        'STAR6', 'STAR7', 'STAR8', 'STAR9', 'STAR10']

    for column in expected_columns:
        assert column in df.columns

    engine = create_engine('postgresql://{}:{}@{}:{}/{}'.format(dbcred.user, dbcred.password, dbcred.host, dbcred.port, 'chicagopolice'))
    df.to_sql('assignments', engine)

    return None


if __name__ == '__main__':
    load('Kalven 16-1105 All Sworn Employees-2.xlsx')
