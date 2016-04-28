import pandas as pd
import psycopg2
from sqlalchemy import create_engine

import dbcred


def load(filename):
    df = pd.read_csv(filename)

    expected_columns = ['LAST_NME', 'FIRST_NME', 'MIDDLE_INITIAL',
                        'SEX_CODE_CD', 'RACE', 'DOBYEAR', 'CURRAGE',
                        'STATUS_I', 'APPOINTED_DATE', 'EMPLOYEE_POSITION_CD',
                        'DESCR', 'CPD_UNIT_ASSIGNED_NO', 'UNITDESCR',
                        'RESIGNATION_DATE', 'STAR1', 'STAR2', 'STAR3', 'STAR4',
                        'STAR5', 'STAR6', 'STAR7', 'STAR8', 'STAR9', 'STAR10']

    for column in expected_columns:
       assert column in df.columns    

    engine = create_engine('postgresql://{}:{}@{}:{}/{}'.format(dbcred.user, dbcred.password, dbcred.host, dbcred.port, 'chicagopolice'))
    df.to_sql('invisinst', engine)

    return None


if __name__=='__main__':
    load('cpd_employees-4-1-16.csv')
