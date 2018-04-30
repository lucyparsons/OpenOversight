import datetime
import os
import re
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
import sys
import tempfile
from traceback import format_exc
from werkzeug import secure_filename

from flask import (abort, render_template, request, redirect, url_for,
                   flash, current_app, jsonify, Markup)
from flask_login import current_user, login_required, login_user

from . import main
from .. import limiter
from ..utils import (grab_officers, roster_lookup, upload_file, compute_hash,
                     serve_image, compute_leaderboard_stats, get_random_image,
                     allowed_file, add_new_assignment, edit_existing_assignment,
                     add_officer_profile, edit_officer_profile)
from .forms import (FindOfficerForm, FindOfficerIDForm, AddUnitForm,
                    FaceTag, AssignmentForm, DepartmentForm, AddOfficerForm,
                    BasicOfficerForm)
from ..models import (db, Image, User, Face, Officer, Assignment, Department,
                      Unit)

from ..auth.forms import LoginForm
from ..auth.utils import admin_required

# Ensure the file is read/write by the creator only
SAVED_UMASK = os.umask(0o077)


def redirect_url(default='index'):
    return request.args.get('next') or request.referrer or url_for(default)


@main.route('/')
@main.route('/index')
def index():
    return render_template('index.html')


@main.route('/browse', methods=['GET'])
def browse():
    departments = Department.query.all()
    return render_template('browse.html', departments=departments)


@main.route('/find', methods=['GET', 'POST'])
def get_officer():
    form = FindOfficerForm()
    if form.validate_on_submit():
        return redirect(url_for('main.get_gallery'), code=307)
    return render_template('input_find_officer.html', form=form)


@main.route('/tagger_find', methods=['GET', 'POST'])
def get_ooid():
    form = FindOfficerIDForm()
    if form.validate_on_submit():
        return redirect(url_for('main.get_tagger_gallery'), code=307)
    return render_template('input_find_ooid.html', form=form)


@main.route('/label', methods=['GET', 'POST'])
def get_started_labeling():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')
    departments = Department.query.all()
    return render_template('label_data.html', departments=departments, form=form)


@main.route('/sort/department/<int:department_id>', methods=['GET', 'POST'])
@login_required
def sort_images(department_id):
    # Select a random unsorted image from the database
    image_query = Image.query.filter_by(contains_cops=None) \
                             .filter_by(department_id=department_id)
    image = get_random_image(image_query)

    if image:
        proper_path = serve_image(image.filepath)
    else:
        proper_path = None
    return render_template('sort.html', image=image, path=proper_path,
                           department_id=department_id)


@main.route('/tutorial')
def get_tutorial():
    return render_template('tutorial.html')


@main.route('/user/<username>')
def profile(username):
    if re.search('^[A-Za-z][A-Za-z0-9_.]*$', username):
        user = User.query.filter_by(username=username).one()
    else:
        abort(404)
    try:
        pref = User.query.filter_by(id=current_user.id).one().dept_pref
        department = Department.query.filter_by(id=pref).one().name
    except NoResultFound:
        department = None
    return render_template('profile.html', user=user, department=department)


@main.route('/officer/<int:officer_id>', methods=['GET', 'POST'])
def officer_profile(officer_id):
    form = AssignmentForm()
    try:
        officer = Officer.query.filter_by(id=officer_id).one()
    except NoResultFound:
        abort(404)
    except:  # noqa
        exception_type, value, full_tback = sys.exc_info()
        current_app.logger.error('Error finding officer: {}'.format(
            ' '.join([str(exception_type), str(value),
                      format_exc(full_tback)])
        ))

    try:
        faces = Face.query.filter_by(officer_id=officer_id).all()
        assignments = Assignment.query.filter_by(officer_id=officer_id).all()
        face_paths = []
        for face in faces:
            face_paths.append(serve_image(face.image.filepath))
    except:  # noqa
        exception_type, value, full_tback = sys.exc_info()
        current_app.logger.error('Error loading officer profile: {}'.format(
            ' '.join([str(exception_type), str(value),
                      format_exc(full_tback)])
        ))

    if form.validate_on_submit() and current_user.is_administrator:
        try:
            add_new_assignment(officer_id, form)
            flash('Added new assignment!')
        except IntegrityError:
            flash('Assignment already exists')
        return redirect(url_for('main.officer_profile',
                                officer_id=officer_id), code=302)
    return render_template('officer.html', officer=officer, paths=face_paths,
                           assignments=assignments, form=form)


@main.route('/officer/<int:officer_id>/assignment/<int:assignment_id>',
            methods=['GET', 'POST'])
@login_required
@admin_required
def edit_assignment(officer_id, assignment_id):
    assignment = Assignment.query.filter_by(id=assignment_id).one()
    form = AssignmentForm(obj=assignment)
    if form.validate_on_submit():
        assignment = edit_existing_assignment(assignment, form)
        flash('Edited officer assignment ID {}'.format(assignment.id))
        return redirect(url_for('main.officer_profile', officer_id=officer_id))
    return render_template('edit_assignment.html', form=form)


@main.route('/user/toggle/<int:uid>', methods=['POST'])
@login_required
@admin_required
def toggle_user(uid):
    try:
        user = User.query.filter_by(id=uid).one()
        if user.is_disabled:
            user.is_disabled = False
        elif not user.is_disabled:
            user.is_disabled = True
        db.session.commit()
        flash('Updated user status')
    except NoResultFound:
        flash('Unknown error occurred')
    return redirect(url_for('main.profile', username=user.username))


@main.route('/image/<int:image_id>')
@login_required
def display_submission(image_id):
    try:
        image = Image.query.filter_by(id=image_id).one()
        proper_path = serve_image(image.filepath)
    except NoResultFound:
        abort(404)
    return render_template('image.html', image=image, path=proper_path)


@main.route('/tag/<int:tag_id>')
@login_required
def display_tag(tag_id):
    try:
        tag = Face.query.filter_by(id=tag_id).one()
        proper_path = serve_image(tag.image.filepath)
    except NoResultFound:
        abort(404)
    return render_template('tag.html', face=tag, path=proper_path)


@main.route('/image/classify/<int:image_id>/<int:contains_cops>',
            methods=['POST'])
@login_required
def classify_submission(image_id, contains_cops):
    try:
        image = Image.query.filter_by(id=image_id).one()
        image.user_id = current_user.id
        if contains_cops == 1:
            image.contains_cops = True
        elif contains_cops == 0:
            image.contains_cops = False
        db.session.commit()
        flash('Updated image classification')
    except:  # noqa
        flash('Unknown error occurred')
        exception_type, value, full_tback = sys.exc_info()
        current_app.logger.error('Error classifying image: {}'.format(
            ' '.join([str(exception_type), str(value),
                      format_exc(full_tback)])
        ))
    return redirect(redirect_url())
    # return redirect(url_for('main.display_submission', image_id=image_id))


@main.route('/department/new', methods=['GET', 'POST'])
@login_required
@admin_required
def add_department():
    form = DepartmentForm()
    if form.validate_on_submit():
        departments = [x[0] for x in db.session.query(Department.name).all()]

        if form.name.data not in departments:
            department = Department(name=form.name.data,
                                    short_name=form.short_name.data)
            db.session.add(department)
            db.session.commit()
            flash('New department {} added to OpenOversight'.format(department.name))
        else:
            flash('Department {} already exists'.format(form.name.data))
        return redirect(url_for('main.get_started_labeling'))
    else:
        return render_template('add_department.html', form=form)


@main.route('/department/<int:department_id>')
def list_officer(department_id, page=1, from_search=False):
    if request.args.get('page'):
        page = int(request.args.get('page'))

    if request.args.get('from_search'):
        if request.args.get('from_search') == 'True':
            from_search = True
        else:
            from_search = False

    OFFICERS_PER_PAGE = int(current_app.config['OFFICERS_PER_PAGE'])
    department = Department.query.filter_by(id=department_id).first()
    if not department:
        abort(404)

    officers = Officer.query.filter(Officer.department_id == department_id) \
        .order_by(Officer.last_name) \
        .paginate(page, OFFICERS_PER_PAGE, False)
    return render_template(
        'list_officer.html',
        department=department,
        officers=officers,
        from_search=from_search)


@main.route('/officer/new', methods=['GET', 'POST'])
@login_required
@admin_required
def add_officer():
    first_department = Department.query.first()
    first_unit = Unit.query.first()
    form = AddOfficerForm(department=first_department, unit=first_unit)
    if form.validate_on_submit():
        officer = add_officer_profile(form)
        flash('New Officer {} added to OpenOversight'.format(officer.last_name))
        return redirect(url_for('main.officer_profile', officer_id=officer.id))
    else:
        return render_template('add_officer.html', form=form)


@main.route('/officer/<int:officer_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_officer(officer_id):
    officer = Officer.query.filter_by(id=officer_id).one()
    form = BasicOfficerForm(obj=officer)
    if form.validate_on_submit():
        officer = edit_officer_profile(officer, form)
        flash('Officer {} edited'.format(officer.last_name))
        return redirect(url_for('main.officer_profile', officer_id=officer.id))
    else:
        return render_template('edit_officer.html', form=form)


@main.route('/unit/new', methods=['GET', 'POST'])
@login_required
@admin_required
def add_unit():
    first_department = Department.query.first()
    form = AddUnitForm(department=first_department)

    if form.validate_on_submit():
        unit = Unit(descrip=form.descrip.data,
                    department_id=form.department.data.id)
        db.session.add(unit)
        db.session.commit()
        flash('New unit {} added to OpenOversight'.format(unit.descrip))
        return redirect(url_for('main.get_started_labeling'))
    else:
        return render_template('add_unit.html', form=form)


@main.route('/tag/delete/<int:tag_id>', methods=['POST'])
@login_required
@admin_required
def delete_tag(tag_id):
    try:
        Face.query.filter_by(id=tag_id).delete()
        db.session.commit()
        flash('Deleted this tag')
    except:  # noqa
        flash('Unknown error occurred')
        exception_type, value, full_tback = sys.exc_info()
        current_app.logger.error('Error classifying image: {}'.format(
            ' '.join([str(exception_type), str(value),
                      format_exc(full_tback)])
        ))
    return redirect(url_for('main.index'))


@main.route('/leaderboard')
@login_required
def leaderboard():
    top_sorters, top_taggers = compute_leaderboard_stats()
    return render_template('leaderboard.html', top_sorters=top_sorters,
                           top_taggers=top_taggers)


@main.route('/cop_face/department/<int:department_id>/image/<int:image_id>',
            methods=['GET', 'POST'])
@main.route('/cop_face/image/<int:image_id>', methods=['GET', 'POST'])
@main.route('/cop_face/department/<int:department_id>', methods=['GET', 'POST'])
@main.route('/cop_face/', methods=['GET', 'POST'])
@login_required
def label_data(department_id=None, image_id=None):
    if department_id:
        department = Department.query.filter_by(id=department_id).one()
        if image_id:
            image = Image.query.filter_by(id=image_id) \
                               .filter_by(department_id=department_id).one()
        else:  # Get a random image from that department
            image_query = Image.query.filter_by(contains_cops=True) \
                               .filter_by(department_id=department_id) \
                               .filter_by(is_tagged=False)
            image = get_random_image(image_query)
    else:
        department = None
        if image_id:
            image = Image.query.filter_by(id=image_id).one()
        else:  # Select a random untagged image from the entire database
            image_query = Image.query.filter_by(contains_cops=True) \
                               .filter_by(is_tagged=False)
            image = get_random_image(image_query)

    if image:
        proper_path = serve_image(image.filepath)
    else:
        proper_path = None

    form = FaceTag()
    if form.validate_on_submit():
        officer_exists = Officer.query.filter_by(id=form.officer_id.data).first()
        existing_tag = db.session.query(Face) \
                         .filter(Face.officer_id == form.officer_id.data) \
                         .filter(Face.img_id == form.image_id.data).first()
        if not officer_exists:
            flash('Invalid officer ID. Please select a valid OpenOversight ID!')
        elif not existing_tag:
            new_tag = Face(officer_id=form.officer_id.data,
                           img_id=form.image_id.data,
                           face_position_x=form.dataX.data,
                           face_position_y=form.dataY.data,
                           face_width=form.dataWidth.data,
                           face_height=form.dataHeight.data,
                           user_id=current_user.id)
            db.session.add(new_tag)
            db.session.commit()
            flash('Tag added to database')
        else:
            flash('Tag already exists between this officer and image! Tag not added.')

    return render_template('cop_face.html', form=form,
                           image=image, path=proper_path,
                           department=department)


@main.route('/image/tagged/<int:image_id>')
@login_required
def complete_tagging(image_id):
    # Select a random untagged image from the database
    image = Image.query.filter_by(id=image_id).one()
    image.is_tagged = True
    db.session.commit()
    flash('Marked image as completed.')
    return redirect(url_for('main.label_data'))


@main.route('/tagger_gallery/<int:page>', methods=['GET', 'POST'])
@main.route('/tagger_gallery', methods=['GET', 'POST'])
def get_tagger_gallery(page=1):
    form = FindOfficerIDForm()
    if form.validate_on_submit():
        OFFICERS_PER_PAGE = int(current_app.config['OFFICERS_PER_PAGE'])
        form_data = form.data
        officers = roster_lookup(form_data).paginate(page, OFFICERS_PER_PAGE, False)
        return render_template('tagger_gallery.html',
                               officers=officers,
                               form=form,
                               form_data=form_data)
    else:
        return redirect(url_for('main.get_ooid'), code=307)


@main.route('/gallery/<int:page>', methods=['GET', 'POST'])
@main.route('/gallery', methods=['GET', 'POST'])
def get_gallery(page=1):
    form = FindOfficerForm()
    if form.validate_on_submit():
        OFFICERS_PER_PAGE = int(current_app.config['OFFICERS_PER_PAGE'])
        form_data = form.data
        officers = grab_officers(form_data).paginate(page, OFFICERS_PER_PAGE, False)
        # If no officers are found, go to a list of all department officers
        if not officers.items:
            return redirect(url_for(
                'main.list_officer',
                department_id=form_data['dept'].id,
                from_search=True)
            )

        return render_template('gallery.html',
                               officers=officers,
                               form=form,
                               form_data=form_data)
    else:
        return redirect(url_for('main.get_officer'))


@main.route('/complaint', methods=['GET', 'POST'])
def submit_complaint():
    return render_template('complaint.html',
                           officer_first_name=request.args.get('officer_first_name'),
                           officer_last_name=request.args.get('officer_last_name'),
                           officer_middle_initial=request.args.get('officer_middle_name'),
                           officer_star=request.args.get('officer_star'),
                           officer_image=request.args.get('officer_image'))


@main.route('/submit', methods=['GET', 'POST'])
@limiter.limit('5/minute')
def submit_data():
    # try to use preferred department if available
    try:
        if User.query.filter_by(id=current_user.id).one().dept_pref:
            flash(Markup('Want to submit for another department? Change your <a href="/auth/change-dept/">default department</a>.'))
            department = User.query.filter_by(id=current_user.id).one().dept_pref
            return redirect(url_for('main.submit_department_images', department_id=department))
        else:
            departments = Department.query.all()
            return render_template('submit_deptselect.html', departments=departments)
    # that is, an anonymous user has no id attribute
    except AttributeError:
        departments = Department.query.all()
        return render_template('submit_deptselect.html', departments=departments)


@main.route('/submit/department/<int:department_id>', methods=['GET', 'POST'])
@limiter.limit('5/minute')
def submit_department_images(department_id=1):
    department = Department.query.filter_by(id=department_id).one()
    return render_template('submit_department.html', department=department)


@main.route('/upload/department/<int:department_id>', methods=['POST'])
@limiter.limit('250/minute')
def upload(department_id):
    file_to_upload = request.files['file']
    if not allowed_file(file_to_upload.filename):
        return jsonify(error="File type not allowed!"), 415
    original_filename = secure_filename(file_to_upload.filename)
    image_data = file_to_upload.read()

    # See if there is a matching photo already in the db
    hash_img = compute_hash(image_data)
    hash_found = Image.query.filter_by(hash_img=hash_img).first()
    if hash_found:
        return jsonify(error="Image already uploaded to OpenOversight!"), 400

    # Generate new filename
    file_extension = original_filename.split('.')[-1]
    new_filename = '{}.{}'.format(hash_img, file_extension)

    # Save temporarily on local filesystem
    tmpdir = tempfile.mkdtemp()
    safe_local_path = os.path.join(tmpdir, new_filename)
    with open(safe_local_path, 'w') as tmp:
        tmp.write(image_data)
    os.umask(SAVED_UMASK)

    # Upload file from local filesystem to S3 bucket and delete locally
    try:
        url = upload_file(safe_local_path, original_filename,
                          new_filename)
        # Update the database to add the image
        new_image = Image(filepath=url, hash_img=hash_img, is_tagged=False,
                          date_image_inserted=datetime.datetime.now(),
                          department_id=department_id,
                          # TODO: Get the following field from exif data
                          date_image_taken=datetime.datetime.now())
        db.session.add(new_image)
        db.session.commit()
        return jsonify(success="Success!"), 200
    except:  # noqa
        exception_type, value, full_tback = sys.exc_info()
        current_app.logger.error('Error uploading to S3: {}'.format(
            ' '.join([str(exception_type), str(value),
                      format_exc(full_tback)])
        ))
        return jsonify(error="Server error encountered. Try again later."), 500
    os.remove(safe_local_path)
    os.rmdir(tmpdir)


@main.route('/about')
def about_oo():
    return render_template('about.html')


@main.route('/privacy')
def privacy_oo():
    return render_template('privacy.html')


@main.route('/shutdown')    # pragma: no cover
def server_shutdown():      # pragma: no cover
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'
