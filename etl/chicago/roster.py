import pandas as pd
import psycopg2
from sqlalchemy import create_engine

import dbcred


def load(filename):
    df = pd.read_excel(filename)

    expected_columns = ['Last Name', 'First Name', 'Middle Initial',
                        'Star No.', 'Current Rank', 'Gender', 'Race',
                        'Date of Employment']
    for column in expected_columns:
       assert column in df.columns    

    # 'Last Name' has some columns already
    df.dropna(subset = ['First Name'], inplace=True)

    engine = create_engine('postgresql://{}:{}@{}:{}/{}'.format(dbcred.user, dbcred.password, dbcred.host, dbcred.port, 'chicagopolice'))
    df.to_sql('roster', engine)

    return None


if __name__=='__main__':
    load('10467-FOIA16-0612-Farr-_Sworn.xls')
