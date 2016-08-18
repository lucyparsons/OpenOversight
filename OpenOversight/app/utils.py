import config 

def grab_officers(form, engine):
    where_clauses = []

    if form['race'] in ('BLACK', 'WHITE', 'ASIAN', 'HISPANIC', 'PACIFIC ISLANDER'):
        where_clauses.append("race like '%%{}%%'".format(form['race']))
    if form['gender'] in ('M', 'F'):
        where_clauses.append("gender = '{}'".format(form['gender']))

    base_query = 'SELECT officer_id, first_name, middle_initial, last_name from officers.roster'

    if where_clauses != []:
        where_clause = ' and '.join(where_clauses)
        full_query = '{} where {}'.format(base_query, where_clause)
    else:
        full_query = base_query

    return engine.execute(full_query)


def grab_officer_face(id, engine):
    pass
    return None


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in config.ALLOWED_EXTENSIONS
