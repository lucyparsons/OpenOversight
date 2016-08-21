import config
import datetime


def grab_officers(form, engine):
    where_clauses = []

    if form['race'] in ('BLACK', 'WHITE', 'ASIAN', 'HISPANIC', 'PACIFIC ISLANDER'):
        where_clauses.append("race like '%%{}%%'".format(form['race']))
    if form['gender'] in ('M', 'F'):
        where_clauses.append("gender = '{}'".format(form['gender']))

    current_year = datetime.datetime.now().year
    min_birth_year = current_year - int(form['min_age'])
    max_birth_year = current_year - int(form['max_age'])

    where_clause = ' AND '.join(where_clauses)
    query = ('SELECT officer_id, first_name, middle_initial, last_name, birth_year '
             'FROM officers.roster '
             'WHERE ((birth_year > {} AND birth_year < {}) '
             'OR birth_year is null) AND {}').format(min_birth_year, max_birth_year, where_clause)

    return engine.execute(query)


def grab_officer_face(id, engine):
    pass
    return 'blah'


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in config.ALLOWED_EXTENSIONS
