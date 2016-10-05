import config
import datetime


def grab_officers(form, engine):
    where_clauses = []

    if form['race'] in ('BLACK', 'WHITE', 'ASIAN', 'HISPANIC', 'PACIFIC ISLANDER'):
        where_clauses.append("race like '%%{}%%'".format(form['race']))
    if form['gender'] in ('M', 'F'):
        where_clauses.append("gender = '{}'".format(form['gender']))
    if form['rank'] =='PO':
        where_clauses.append("(rank like '%%PO%%' or rank like '%%POLICE OFFICER%%' or rank is null)")
    if form['rank'] in ('FIELD', 'SERGEANT', 'LIEUTENANT', 'CAPTAIN', 'COMMANDER', 
                        'DEP CHIEF', 'CHIEF', 'DEPUTY SUPT', 'SUPT OF POLICE'):
        where_clauses.append("(rank like '%%{}%%' or rank is null)".format(form['rank']))

    current_year = datetime.datetime.now().year
    min_birth_year = current_year - int(form['min_age'])
    max_birth_year = current_year - int(form['max_age'])

    where_clause = ' AND '.join(where_clauses)
    if len(where_clause) > 0:
        where_clause = ' AND {}'.format(where_clause)

    query = ('SELECT DISTINCT ON (t1.officer_id) '
             't1.first_name, '
             't1.middle_initial, t1.last_name, '
             't1.race, t1.gender, t1.officer_id, '
             't1.birth_year, t2.rank, t2.star_no, t2.start_date, t2.unit '
             'FROM officers.roster t1 '
             'INNER JOIN officers.assignments t2 '
             'ON t1.officer_id = t2.officer_id '
             'WHERE ((t1.birth_year <= {} AND t1.birth_year >= {}) '
             'OR t1.birth_year is null) {} '
             'ORDER BY t1.officer_id, t2.start_date DESC').format(min_birth_year, max_birth_year, where_clause)
    return engine.execute(query)


def grab_officer_faces(officer_ids, engine):
    if len(officer_ids) == 0:
        return []

    query = ('SELECT officer_id, t1.filepath FROM officers.raw_images t1 '
             'INNER JOIN officers.faces t2 '
             'ON t1.img_id = t2.img_id '
             'WHERE officer_id in ({})').format(", ".join([str(x) for x in officer_ids]))
    matches = engine.execute(query)

    officer_images = {}
    for match in matches:
        officer_images.update({match[0]: match[1]})
    
    for officer_id in officer_ids:
        if officer_id not in officer_images.keys():
            officer_images.update({officer_id: 'http://placehold.it/200x200'})

    return officer_images


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in config.ALLOWED_EXTENSIONS
