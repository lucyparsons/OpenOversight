import datetime
import os
import re
import sys
from http import HTTPMethod, HTTPStatus
from traceback import format_exc

from flask import (
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import contains_eager, joinedload, selectinload
from sqlalchemy.orm.exc import NoResultFound

from OpenOversight.app.utils.cloud import crop_image, upload_image_to_s3_and_store_in_db
from OpenOversight.app.utils.db import (
    add_department_query,
    add_unit_query,
    compute_leaderboard_stats,
    dept_choices,
    unit_choices,
)
from OpenOversight.app.utils.forms import (
    add_new_assignment,
    add_officer_profile,
    create_description,
    create_incident,
    create_note,
    edit_existing_assignment,
    edit_officer_profile,
    filter_by_form,
    set_dynamic_default,
)
from OpenOversight.app.utils.general import (
    ac_can_edit_officer,
    allowed_file,
    get_or_create,
    get_random_image,
    replace_list,
    serve_image,
    validate_redirect_url,
)

from .. import limiter, sitemap
from ..auth.forms import LoginForm
from ..auth.utils import ac_or_admin_required, admin_required
from ..models import (
    Assignment,
    Department,
    Description,
    Face,
    Image,
    Incident,
    Job,
    LicensePlate,
    Link,
    Location,
    Note,
    Officer,
    Salary,
    Unit,
    User,
    db,
)
from . import downloads, main
from .choices import AGE_CHOICES, GENDER_CHOICES, RACE_CHOICES
from .forms import (
    AddImageForm,
    AddOfficerForm,
    AddUnitForm,
    AssignmentForm,
    BrowseForm,
    DepartmentForm,
    EditDepartmentForm,
    EditOfficerForm,
    EditTextForm,
    FaceTag,
    FindOfficerForm,
    IncidentForm,
    IncidentListForm,
    OfficerLinkForm,
    SalaryForm,
    TextForm,
)
from .model_view import ModelView


# Ensure the file is read/write by the creator only
SAVED_UMASK = os.umask(0o077)

sitemap_endpoints = []


def sitemap_include(view):
    sitemap_endpoints.append(view.__name__)
    return view


@sitemap.register_generator
def static_routes():
    for endpoint in sitemap_endpoints:
        yield "main." + endpoint, {}


def redirect_url(default="index"):
    return (
        validate_redirect_url(session.get("next"))
        or request.referrer
        or url_for(default)
    )


@sitemap_include
@main.route("/")
@main.route("/index")
def index():
    return render_template("index.html")


@sitemap_include
@main.route("/browse", methods=[HTTPMethod.GET])
def browse():
    departments = Department.query.filter(Department.officers.any())
    return render_template("browse.html", departments=departments)


@sitemap_include
@main.route("/find", methods=[HTTPMethod.GET, HTTPMethod.POST])
def get_officer():
    jsloads = ["js/find_officer.js"]
    form = FindOfficerForm()

    depts_dict = [dept_choice.toCustomDict() for dept_choice in dept_choices()]

    if getattr(current_user, "dept_pref_rel", None):
        set_dynamic_default(form.dept, current_user.dept_pref_rel)

    if form.validate_on_submit():
        return redirect(
            url_for(
                "main.list_officer",
                department_id=form.data["dept"].id,
                race=form.data["race"] if form.data["race"] != "Not Sure" else None,
                gender=form.data["gender"]
                if form.data["gender"] != "Not Sure"
                else None,
                rank=form.data["rank"] if form.data["rank"] != "Not Sure" else None,
                unit=form.data["unit"] if form.data["unit"] != "Not Sure" else None,
                current_job=form.data["current_job"] or None,
                # set to None if False
                min_age=form.data["min_age"],
                max_age=form.data["max_age"],
                first_name=form.data["first_name"],
                last_name=form.data["last_name"],
                badge=form.data["badge"],
                unique_internal_identifier=form.data["unique_internal_identifier"],
            ),
            code=HTTPStatus.FOUND,
        )
    else:
        current_app.logger.info(form.errors)
    return render_template(
        "input_find_officer.html", form=form, depts_dict=depts_dict, jsloads=jsloads
    )


@sitemap_include
@main.route("/label", methods=[HTTPMethod.GET, HTTPMethod.POST])
def get_started_labeling():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.by_email(form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(url_for("main.get_started_labeling"))
        flash("Invalid username or password.")
    else:
        current_app.logger.info(form.errors)
    departments = Department.query.all()
    return render_template("label_data.html", departments=departments, form=form)


@main.route(
    "/sort/department/<int:department_id>", methods=[HTTPMethod.GET, HTTPMethod.POST]
)
@login_required
def sort_images(department_id):
    # Select a random unsorted image from the database
    image_query = Image.query.filter_by(contains_cops=None).filter_by(
        department_id=department_id
    )
    image = get_random_image(image_query)

    if image:
        proper_path = serve_image(image.filepath)
    else:
        proper_path = None
    return render_template(
        "sort.html", image=image, path=proper_path, department_id=department_id
    )


@sitemap_include
@main.route("/tutorial")
def get_tutorial():
    return render_template("tutorial.html")


@main.route("/user/<username>")
@login_required
def profile(username):
    if re.search("^[A-Za-z][A-Za-z0-9_.]*$", username):
        user = User.by_username(username).one()
    else:
        abort(HTTPStatus.NOT_FOUND)
    try:
        pref = User.query.filter_by(id=current_user.get_id()).one().dept_pref
        department = Department.query.filter_by(id=pref).one().name
    except NoResultFound:
        department = None
    return render_template("profile.html", user=user, department=department)


@main.route("/officer/<int:officer_id>", methods=[HTTPMethod.GET, HTTPMethod.POST])
def officer_profile(officer_id):
    form = AssignmentForm()
    try:
        officer = Officer.query.filter_by(id=officer_id).one()
    except NoResultFound:
        abort(HTTPStatus.NOT_FOUND)
    except:  # noqa: E722
        exception_type, value, full_tback = sys.exc_info()
        current_app.logger.error(
            "Error finding officer: {}".format(
                " ".join([str(exception_type), str(value), format_exc()])
            )
        )
    form.job_title.query = (
        Job.query.filter_by(department_id=officer.department_id)
        .order_by(Job.order.asc())
        .all()
    )

    try:
        faces = (
            Face.query.filter_by(officer_id=officer_id)
            .order_by(Face.featured.desc())
            .all()
        )
        assignments = Assignment.query.filter_by(officer_id=officer_id).all()
        face_paths = []
        for face in faces:
            face_paths.append(serve_image(face.image.filepath))
        if not face_paths:
            # Add in the placeholder image if no faces are found
            face_paths = [url_for("static", filename="images/placeholder.png")]
    except:  # noqa: E722
        exception_type, value, full_tback = sys.exc_info()
        current_app.logger.error(
            "Error loading officer profile: {}".format(
                " ".join([str(exception_type), str(value), format_exc()])
            )
        )
    if faces:
        officer.image_url = faces[0].image.filepath
        if not officer.image_url.startswith("http"):
            officer.image_url = url_for(
                "static",
                filename=faces[0].image.filepath.replace("/static/", ""),
            )
        if faces[0].face_width and faces[0].face_height:
            officer.image_width = faces[0].face_width
            officer.image_height = faces[0].face_height
    return render_template(
        "officer.html",
        officer=officer,
        paths=face_paths,
        faces=faces,
        assignments=assignments,
        form=form,
    )


@sitemap.register_generator
def sitemap_officers():
    for officer in Officer.query.all():
        yield "main.officer_profile", {"officer_id": officer.id}


@main.route("/officer/<int:officer_id>/assignment/new", methods=[HTTPMethod.POST])
@ac_or_admin_required
def add_assignment(officer_id):
    form = AssignmentForm()
    officer = Officer.query.filter_by(id=officer_id).first()
    form.job_title.query = (
        Job.query.filter_by(department_id=officer.department_id)
        .order_by(Job.order.asc())
        .all()
    )
    if not officer:
        flash("Officer not found")
        abort(HTTPStatus.NOT_FOUND)

    if form.validate_on_submit():
        if current_user.is_administrator or (
            current_user.is_area_coordinator
            and officer.department_id == current_user.ac_department_id
        ):
            try:
                add_new_assignment(officer_id, form)
                flash("Added new assignment!")
            except IntegrityError:
                flash("Assignment already exists")
            return redirect(
                url_for("main.officer_profile", officer_id=officer_id),
                code=HTTPStatus.FOUND,
            )
        elif (
            current_user.is_area_coordinator
            and not officer.department_id == current_user.ac_department_id
        ):
            abort(HTTPStatus.FORBIDDEN)
    else:
        current_app.logger.info(form.errors)
        flash("Error: " + str(form.errors))

        return redirect(url_for("main.officer_profile", officer_id=officer_id))


@main.route(
    "/officer/<int:officer_id>/assignment/<int:assignment_id>",
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)
@login_required
@ac_or_admin_required
def edit_assignment(officer_id, assignment_id):
    officer = Officer.query.filter_by(id=officer_id).one()

    if current_user.is_area_coordinator and not current_user.is_administrator:
        if not ac_can_edit_officer(officer, current_user):
            abort(HTTPStatus.FORBIDDEN)

    assignment = Assignment.query.filter_by(id=assignment_id).one()
    form = AssignmentForm(obj=assignment)
    form.job_title.query = (
        Job.query.filter_by(department_id=officer.department_id)
        .order_by(Job.order.asc())
        .all()
    )
    form.job_title.data = Job.query.filter_by(id=assignment.job_id).one()
    form.unit.query = unit_choices(officer.department_id)
    if form.unit.data and type(form.unit.data) == int:
        form.unit.data = Unit.query.filter_by(id=form.unit.data).one()
    if form.validate_on_submit():
        form.job_title.data = Job.query.filter_by(
            id=int(form.job_title.raw_data[0])
        ).one()
        assignment = edit_existing_assignment(assignment, form)
        flash("Edited officer assignment ID {}".format(assignment.id))
        return redirect(url_for("main.officer_profile", officer_id=officer_id))
    else:
        current_app.logger.info(form.errors)
    return render_template("edit_assignment.html", form=form)


@main.route(
    "/officer/<int:officer_id>/salary/new", methods=[HTTPMethod.GET, HTTPMethod.POST]
)
@ac_or_admin_required
def add_salary(officer_id):
    form = SalaryForm()
    officer = Officer.query.filter_by(id=officer_id).first()
    if not officer:
        flash("Officer not found")
        abort(HTTPStatus.NOT_FOUND)

    if form.validate_on_submit() and (
        current_user.is_administrator
        or (
            current_user.is_area_coordinator
            and officer.department_id == current_user.ac_department_id
        )
    ):
        try:
            new_salary = Salary(
                officer_id=officer_id,
                salary=form.salary.data,
                overtime_pay=form.overtime_pay.data,
                year=form.year.data,
                is_fiscal_year=form.is_fiscal_year.data,
            )
            db.session.add(new_salary)
            db.session.commit()
            flash("Added new salary!")
        except IntegrityError as e:
            db.session.rollback()
            flash("Error adding new salary: {}".format(e))
        return redirect(
            url_for("main.officer_profile", officer_id=officer_id),
            code=HTTPStatus.FOUND,
        )
    elif (
        current_user.is_area_coordinator
        and not officer.department_id == current_user.ac_department_id
    ):
        abort(HTTPStatus.FORBIDDEN)
    else:
        return render_template("add_edit_salary.html", form=form)


@main.route(
    "/officer/<int:officer_id>/salary/<int:salary_id>",
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)
@login_required
@ac_or_admin_required
def edit_salary(officer_id, salary_id):
    if current_user.is_area_coordinator and not current_user.is_administrator:
        officer = Officer.query.filter_by(id=officer_id).one()
        if not ac_can_edit_officer(officer, current_user):
            abort(HTTPStatus.FORBIDDEN)

    salary = Salary.query.filter_by(id=salary_id).one()
    form = SalaryForm(obj=salary)
    if form.validate_on_submit():
        form.populate_obj(salary)
        db.session.add(salary)
        db.session.commit()
        flash("Edited officer salary ID {}".format(salary.id))
        return redirect(url_for("main.officer_profile", officer_id=officer_id))
    else:
        current_app.logger.info(form.errors)
    return render_template("add_edit_salary.html", form=form, update=True)


@main.route("/image/<int:image_id>")
@login_required
def display_submission(image_id):
    try:
        image = Image.query.filter_by(id=image_id).one()
        proper_path = serve_image(image.filepath)
    except NoResultFound:
        abort(HTTPStatus.NOT_FOUND)
    return render_template("image.html", image=image, path=proper_path)


@main.route("/tag/<int:tag_id>")
def display_tag(tag_id):
    jsloads = ["js/tag.js"]
    try:
        tag = Face.query.filter_by(id=tag_id).one()
        proper_path = serve_image(tag.original_image.filepath)
    except NoResultFound:
        abort(HTTPStatus.NOT_FOUND)
    return render_template("tag.html", face=tag, path=proper_path, jsloads=jsloads)


@main.route(
    "/image/classify/<int:image_id>/<int:contains_cops>", methods=[HTTPMethod.POST]
)
@login_required
def classify_submission(image_id, contains_cops):
    try:
        image = Image.query.filter_by(id=image_id).one()
        if image.contains_cops is not None and not current_user.is_administrator:
            flash("Only administrator can re-classify image")
            return redirect(redirect_url())
        image.user_id = current_user.get_id()
        if contains_cops == 1:
            image.contains_cops = True
        elif contains_cops == 0:
            image.contains_cops = False
        db.session.commit()
        flash("Updated image classification")
    except:  # noqa: E722
        flash("Unknown error occurred")
        exception_type, value, full_tback = sys.exc_info()
        current_app.logger.error(
            "Error classifying image: {}".format(
                " ".join([str(exception_type), str(value), format_exc()])
            )
        )
    return redirect(redirect_url())
    # return redirect(url_for('main.display_submission', image_id=image_id))


@main.route("/department/new", methods=[HTTPMethod.GET, HTTPMethod.POST])
@login_required
@admin_required
def add_department():
    jsloads = ["js/jquery-ui.min.js", "js/deptRanks.js"]
    form = DepartmentForm()
    if form.validate_on_submit():
        departments = [x[0] for x in db.session.query(Department.name).all()]

        if form.name.data not in departments:
            department = Department(
                name=form.name.data, short_name=form.short_name.data
            )
            db.session.add(department)
            db.session.flush()
            db.session.add(
                Job(job_title="Not Sure", order=0, department_id=department.id)
            )
            db.session.flush()
            if form.jobs.data:
                order = 1
                for job in form.data["jobs"]:
                    if job:
                        db.session.add(
                            Job(
                                job_title=job,
                                order=order,
                                is_sworn_officer=True,
                                department_id=department.id,
                            )
                        )
                        order += 1
                db.session.commit()
            flash("New department {} added to OpenOversight".format(department.name))
        else:
            flash("Department {} already exists".format(form.name.data))
        return redirect(url_for("main.get_started_labeling"))
    else:
        current_app.logger.info(form.errors)
        return render_template("add_edit_department.html", form=form, jsloads=jsloads)


@main.route(
    "/department/<int:department_id>/edit", methods=[HTTPMethod.GET, HTTPMethod.POST]
)
@login_required
@admin_required
def edit_department(department_id):
    jsloads = ["js/jquery-ui.min.js", "js/deptRanks.js"]
    department = Department.query.get_or_404(department_id)
    previous_name = department.name
    form = EditDepartmentForm(obj=department)
    original_ranks = department.jobs
    if form.validate_on_submit():
        new_name = form.name.data
        if new_name != previous_name:
            if Department.query.filter_by(name=new_name).count() > 0:
                flash("Department {} already exists".format(new_name))
                return redirect(
                    url_for("main.edit_department", department_id=department_id)
                )
        department.name = new_name
        department.short_name = form.short_name.data
        db.session.flush()
        if form.jobs.data:
            new_ranks = []
            order = 1
            for rank in form.data["jobs"]:
                if rank:
                    new_ranks.append((rank, order))
                    order += 1
            updated_ranks = form.jobs.data
            if len(updated_ranks) < len(original_ranks):
                deleted_ranks = [
                    rank
                    for rank in original_ranks
                    if rank.job_title not in updated_ranks
                ]
                if (
                    Assignment.query.filter(
                        Assignment.job_id.in_([rank.id for rank in deleted_ranks])
                    ).count()
                    == 0
                ):
                    for rank in deleted_ranks:
                        db.session.delete(rank)
                else:
                    failed_deletions = []
                    for rank in deleted_ranks:
                        if (
                            Assignment.query.filter(
                                Assignment.job_id.in_([rank.id])
                            ).count()
                            != 0
                        ):
                            failed_deletions.append(rank)
                    for rank in failed_deletions:
                        flash(
                            "You attempted to delete a rank, {}, that is still in use".format(
                                rank
                            )
                        )
                    return redirect(
                        url_for("main.edit_department", department_id=department_id)
                    )

            for (new_rank, order) in new_ranks:
                existing_rank = Job.query.filter_by(
                    department_id=department_id, job_title=new_rank
                ).one_or_none()
                if existing_rank:
                    existing_rank.is_sworn_officer = True
                    existing_rank.order = order
                else:
                    db.session.add(
                        Job(
                            job_title=new_rank,
                            order=order,
                            is_sworn_officer=True,
                            department_id=department_id,
                        )
                    )
            db.session.commit()

        flash("Department {} edited".format(department.name))
        return redirect(url_for("main.list_officer", department_id=department.id))
    else:
        current_app.logger.info(form.errors)
        return render_template(
            "add_edit_department.html", form=form, update=True, jsloads=jsloads
        )


@main.route("/department/<int:department_id>")
def list_officer(
    department_id,
    page=1,
    race=None,
    gender=None,
    rank=None,
    min_age="16",
    max_age="100",
    last_name=None,
    first_name=None,
    badge=None,
    unique_internal_identifier=None,
    unit=None,
    current_job=None,
):
    jsloads = ["js/select2.min.js", "js/list_officer.js"]

    form = BrowseForm()
    form.rank.query = (
        Job.query.filter_by(department_id=department_id, is_sworn_officer=True)
        .order_by(Job.order.asc())
        .all()
    )
    form_data = form.data
    form_data["race"] = race or []
    form_data["gender"] = gender or []
    form_data["rank"] = rank or []
    form_data["min_age"] = min_age
    form_data["max_age"] = max_age
    form_data["last_name"] = last_name
    form_data["first_name"] = first_name
    form_data["badge"] = badge
    form_data["unit"] = unit or []
    form_data["current_job"] = current_job
    form_data["unique_internal_identifier"] = unique_internal_identifier

    department = Department.query.filter_by(id=department_id).first()
    if not department:
        abort(HTTPStatus.NOT_FOUND)

    age_range = {ac[0] for ac in AGE_CHOICES}

    # Set form data based on URL
    if (min_age_arg := request.args.get("min_age")) and min_age_arg in age_range:
        form_data["min_age"] = min_age_arg
    if (max_age_arg := request.args.get("max_age")) and max_age_arg in age_range:
        form_data["max_age"] = max_age_arg
    if page_arg := request.args.get("page"):
        page = int(page_arg)
    if last_name_arg := request.args.get("last_name"):
        form_data["last_name"] = last_name_arg
    if first_name_arg := request.args.get("first_name"):
        form_data["first_name"] = first_name_arg
    if badge_arg := request.args.get("badge"):
        form_data["badge"] = badge_arg
    if uid := request.args.get("unique_internal_identifier"):
        form_data["unique_internal_identifier"] = uid
    if (races := request.args.getlist("race")) and all(
        race in [rc[0] for rc in RACE_CHOICES] for race in races
    ):
        form_data["race"] = races
    if (genders := request.args.getlist("gender")) and all(
        # Every time you complain we add a new gender
        gender in [gc[0] for gc in GENDER_CHOICES]
        for gender in genders
    ):
        form_data["gender"] = genders

    unit_choices = ["Not Sure"] + [
        uc[0]
        for uc in db.session.query(Unit.descrip)
        .filter_by(department_id=department_id)
        .order_by(Unit.descrip.asc())
        .all()
    ]
    rank_choices = [
        jc[0]
        for jc in db.session.query(Job.job_title, Job.order)
        .filter_by(department_id=department_id)
        .order_by(Job.job_title)
        .all()
    ]
    if (units := request.args.getlist("unit")) and all(
        unit in unit_choices for unit in units
    ):
        form_data["unit"] = units
    if (ranks := request.args.getlist("rank")) and all(
        rank in rank_choices for rank in ranks
    ):
        form_data["rank"] = ranks
    if current_job_arg := request.args.get("current_job"):
        form_data["current_job"] = current_job_arg

    officers = filter_by_form(form_data, Officer.query, department_id).filter(
        Officer.department_id == department_id
    )
    officers = officers.options(selectinload(Officer.face))
    officers = officers.order_by(Officer.last_name, Officer.first_name, Officer.id)
    officers = officers.paginate(
        page=page, per_page=current_app.config["OFFICERS_PER_PAGE"], error_out=False
    )
    for officer in officers.items:
        officer_face = sorted(officer.face, key=lambda x: x.featured, reverse=True)

        # could do some extra work to not lazy load images but load them all together
        # but we would want to ensure to only load the first picture of each officer
        if officer_face and officer_face[0].image:
            officer.image = officer_face[0].image.filepath

    choices = {
        "race": RACE_CHOICES,
        "gender": GENDER_CHOICES,
        "rank": [(rc, rc) for rc in rank_choices],
        "unit": [(uc, uc) for uc in unit_choices],
    }

    next_url = url_for(
        "main.list_officer",
        department_id=department.id,
        page=officers.next_num,
        race=form_data["race"],
        gender=form_data["gender"],
        rank=form_data["rank"],
        min_age=form_data["min_age"],
        max_age=form_data["max_age"],
        last_name=form_data["last_name"],
        first_name=form_data["first_name"],
        badge=form_data["badge"],
        unique_internal_identifier=form_data["unique_internal_identifier"],
        unit=form_data["unit"],
        current_job=form_data["current_job"],
    )
    prev_url = url_for(
        "main.list_officer",
        department_id=department.id,
        page=officers.prev_num,
        race=form_data["race"],
        gender=form_data["gender"],
        rank=form_data["rank"],
        min_age=form_data["min_age"],
        max_age=form_data["max_age"],
        last_name=form_data["last_name"],
        first_name=form_data["first_name"],
        badge=form_data["badge"],
        unique_internal_identifier=form_data["unique_internal_identifier"],
        unit=form_data["unit"],
        current_job=form_data["current_job"],
    )

    return render_template(
        "list_officer.html",
        form=form,
        department=department,
        officers=officers,
        form_data=form_data,
        choices=choices,
        next_url=next_url,
        prev_url=prev_url,
        jsloads=jsloads,
    )


@main.route("/department/<int:department_id>/ranks")
@main.route("/ranks")
def get_dept_ranks(department_id=None, is_sworn_officer=None):
    if not department_id:
        department_id = request.args.get("department_id")
    if request.args.get("is_sworn_officer"):
        is_sworn_officer = request.args.get("is_sworn_officer")

    if department_id:
        ranks = Job.query.filter_by(department_id=department_id)
        if is_sworn_officer:
            ranks = ranks.filter_by(is_sworn_officer=True)
        ranks = ranks.order_by(Job.job_title).all()
        rank_list = [(rank.id, rank.job_title) for rank in ranks]
    else:
        ranks = Job.query.all()  # Not filtering by is_sworn_officer
        # Prevent duplicate ranks
        rank_list = sorted(
            set((rank.id, rank.job_title) for rank in ranks),
            key=lambda x: x[1],
        )

    return jsonify(rank_list)


@main.route("/department/<int:department_id>/units")
@main.route("/units")
def get_dept_units(department_id=None):
    if not department_id:
        department_id = request.args.get("department_id")

    if department_id:
        units = Unit.query.filter_by(department_id=department_id)
        units = units.order_by(Unit.descrip).all()
        unit_list = [(unit.id, unit.descrip) for unit in units]
    else:
        units = Unit.query.all()
        # Prevent duplicate units
        unit_list = sorted(
            set((unit.id, unit.descrip) for unit in units),
            key=lambda x: x[1],
        )

    return jsonify(unit_list)


@main.route("/officer/new", methods=[HTTPMethod.GET, HTTPMethod.POST])
@login_required
@ac_or_admin_required
def add_officer():
    jsloads = ["js/dynamic_lists.js", "js/add_officer.js"]
    form = AddOfficerForm()
    for link in form.links:
        link.creator_id.data = current_user.id
    add_unit_query(form, current_user)
    add_department_query(form, current_user)
    set_dynamic_default(form.department, current_user.dept_pref_rel)

    if (
        form.validate_on_submit()
        and not current_user.is_administrator
        and form.department.data.id != current_user.ac_department_id
    ):
        abort(HTTPStatus.FORBIDDEN)
    if form.validate_on_submit():
        # Work around for WTForms limitation with boolean fields in FieldList
        new_formdata = request.form.copy()
        for key in new_formdata.keys():
            if re.fullmatch(r"salaries-\d+-is_fiscal_year", key):
                new_formdata[key] = "y"
        form = AddOfficerForm(new_formdata)
        officer = add_officer_profile(form, current_user)
        flash("New Officer {} added to OpenOversight".format(officer.last_name))
        return redirect(url_for("main.submit_officer_images", officer_id=officer.id))
    else:
        current_app.logger.info(form.errors)
        return render_template("add_officer.html", form=form, jsloads=jsloads)


@main.route("/officer/<int:officer_id>/edit", methods=[HTTPMethod.GET, HTTPMethod.POST])
@login_required
@ac_or_admin_required
def edit_officer(officer_id):
    jsloads = ["js/dynamic_lists.js"]
    officer = Officer.query.filter_by(id=officer_id).one()
    form = EditOfficerForm(obj=officer)

    if request.method == HTTPMethod.GET:
        if officer.race is None:
            form.race.data = "Not Sure"
        if officer.gender is None:
            form.gender.data = "Not Sure"

    if current_user.is_area_coordinator and not current_user.is_administrator:
        if not ac_can_edit_officer(officer, current_user):
            abort(HTTPStatus.FORBIDDEN)

    add_department_query(form, current_user)

    if form.validate_on_submit():
        officer = edit_officer_profile(officer, form)
        flash("Officer {} edited".format(officer.last_name))
        return redirect(url_for("main.officer_profile", officer_id=officer.id))
    else:
        current_app.logger.info(form.errors)
        return render_template("edit_officer.html", form=form, jsloads=jsloads)


@main.route("/unit/new", methods=[HTTPMethod.GET, HTTPMethod.POST])
@login_required
@ac_or_admin_required
def add_unit():
    form = AddUnitForm()
    add_department_query(form, current_user)
    set_dynamic_default(form.department, current_user.dept_pref_rel)

    if form.validate_on_submit():
        unit = Unit(descrip=form.descrip.data, department_id=form.department.data.id)
        db.session.add(unit)
        db.session.commit()
        flash("New unit {} added to OpenOversight".format(unit.descrip))
        return redirect(url_for("main.get_started_labeling"))
    else:
        current_app.logger.info(form.errors)
        return render_template("add_unit.html", form=form)


@main.route("/tag/delete/<int:tag_id>", methods=[HTTPMethod.POST])
@login_required
@ac_or_admin_required
def delete_tag(tag_id):
    tag = Face.query.filter_by(id=tag_id).first()

    if not tag:
        flash("Tag not found")
        abort(HTTPStatus.NOT_FOUND)

    if not current_user.is_administrator and current_user.is_area_coordinator:
        if current_user.ac_department_id != tag.officer.department_id:
            abort(HTTPStatus.FORBIDDEN)

    officer_id = tag.officer_id
    try:
        db.session.delete(tag)
        db.session.commit()
        flash("Deleted this tag")
    except:  # noqa: E722
        flash("Unknown error occurred")
        current_app.logger.exception("Unknown error occurred")

    return redirect(url_for("main.officer_profile", officer_id=officer_id))


@main.route("/tag/set_featured/<int:tag_id>", methods=[HTTPMethod.POST])
@login_required
@ac_or_admin_required
def set_featured_tag(tag_id):
    tag = Face.query.filter_by(id=tag_id).first()

    if not tag:
        flash("Tag not found")
        abort(HTTPStatus.NOT_FOUND)

    if not current_user.is_administrator and current_user.is_area_coordinator:
        if current_user.ac_department_id != tag.officer.department_id:
            abort(HTTPStatus.FORBIDDEN)

    # Set featured=False on all other tags for the same officer
    for face in Face.query.filter_by(officer_id=tag.officer_id).all():
        face.featured = False
    # Then set this tag as featured
    tag.featured = True

    try:
        db.session.commit()
        flash("Successfully set this tag as featured")
    except:  # noqa: E722
        flash("Unknown error occurred")
        exception_type, value, full_tback = sys.exc_info()
        current_app.logger.error(
            "Error setting featured tag: {}".format(
                " ".join([str(exception_type), str(value), format_exc()])
            )
        )
    return redirect(url_for("main.officer_profile", officer_id=tag.officer_id))


@main.route("/leaderboard")
@login_required
def leaderboard():
    top_sorters, top_taggers = compute_leaderboard_stats()
    return render_template(
        "leaderboard.html", top_sorters=top_sorters, top_taggers=top_taggers
    )


@main.route(
    "/cop_face/department/<int:department_id>/image/<int:image_id>",
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)
@main.route("/cop_face/image/<int:image_id>", methods=[HTTPMethod.GET, HTTPMethod.POST])
@main.route(
    "/cop_face/department/<int:department_id>",
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)
@main.route("/cop_face/", methods=[HTTPMethod.GET, HTTPMethod.POST])
@login_required
def label_data(department_id=None, image_id=None):
    jsloads = ["js/cropper.js", "js/tagger.js"]
    if department_id:
        department = Department.query.filter_by(id=department_id).one()
        if image_id:
            image = (
                Image.query.filter_by(id=image_id)
                .filter_by(department_id=department_id)
                .first()
            )
        else:  # Get a random image from that department
            image_query = (
                Image.query.filter_by(contains_cops=True)
                .filter_by(department_id=department_id)
                .filter_by(is_tagged=False)
            )
            image = get_random_image(image_query)
    else:
        department = None
        if image_id:
            image = Image.query.filter_by(id=image_id).one()
        else:  # Select a random untagged image from the entire database
            image_query = Image.query.filter_by(contains_cops=True).filter_by(
                is_tagged=False
            )
            image = get_random_image(image_query)

    if image:
        if image.is_tagged and not current_user.is_administrator:
            flash("This image cannot be tagged anymore")
            return redirect(url_for("main.label_data"))
        proper_path = serve_image(image.filepath)
    else:
        proper_path = None

    form = FaceTag()
    if form.validate_on_submit():
        officer_exists = Officer.query.filter_by(id=form.officer_id.data).first()
        existing_tag = (
            db.session.query(Face)
            .filter(Face.officer_id == form.officer_id.data)
            .filter(Face.original_image_id == form.image_id.data)
            .first()
        )
        if not officer_exists:
            flash("Invalid officer ID. Please select a valid OpenOversight ID!")
        elif department and officer_exists.department_id != department_id:
            flash(
                "The officer is not in {}. Are you sure that is the correct OpenOversight ID?".format(
                    department.name
                )
            )
        elif not existing_tag:
            left = form.dataX.data
            upper = form.dataY.data
            right = left + form.dataWidth.data
            lower = upper + form.dataHeight.data

            cropped_image = crop_image(
                image,
                crop_data=(left, upper, right, lower),
                department_id=department_id,
            )
            cropped_image.contains_cops = True
            cropped_image.is_tagged = True

            if cropped_image:
                new_tag = Face(
                    officer_id=form.officer_id.data,
                    img_id=cropped_image.id,
                    original_image_id=image.id,
                    face_position_x=left,
                    face_position_y=upper,
                    face_width=form.dataWidth.data,
                    face_height=form.dataHeight.data,
                    user_id=current_user.get_id(),
                )
                db.session.add(new_tag)
                db.session.commit()
                flash("Tag added to database")
            else:
                flash("There was a problem saving this tag. Please try again later.")
        else:
            flash("Tag already exists between this officer and image! Tag not added.")
    else:
        current_app.logger.info(form.errors)

    return render_template(
        "cop_face.html",
        form=form,
        image=image,
        path=proper_path,
        department=department,
        jsloads=jsloads,
    )


@main.route("/image/tagged/<int:image_id>")
@login_required
def complete_tagging(image_id):
    # Select a random untagged image from the database
    image = Image.query.filter_by(id=image_id).first()
    if not image:
        abort(HTTPStatus.NOT_FOUND)
    image.is_tagged = True
    db.session.commit()
    flash("Marked image as completed.")
    department_id = request.args.get("department_id")
    if department_id:
        return redirect(url_for("main.label_data", department_id=department_id))
    else:
        return redirect(url_for("main.label_data"))


@main.route("/complaint", methods=[HTTPMethod.GET, HTTPMethod.POST])
def submit_complaint():
    return render_template(
        "complaint.html",
        officer_first_name=request.args.get("officer_first_name"),
        officer_last_name=request.args.get("officer_last_name"),
        officer_middle_initial=request.args.get("officer_middle_name"),
        officer_star=request.args.get("officer_star"),
        officer_image=request.args.get("officer_image"),
    )


@sitemap_include
@main.route("/submit", methods=[HTTPMethod.GET, HTTPMethod.POST])
@limiter.limit("5/minute")
def submit_data():
    preferred_dept_id = Department.query.first().id
    # try to use preferred department if available
    try:
        if User.query.filter_by(id=current_user.get_id()).one().dept_pref:
            preferred_dept_id = (
                User.query.filter_by(id=current_user.get_id()).one().dept_pref
            )
            form = AddImageForm()
        else:
            form = AddImageForm()
        return render_template(
            "submit_image.html", form=form, preferred_dept_id=preferred_dept_id
        )
    # that is, an anonymous user has no id attribute
    except (AttributeError, NoResultFound):
        preferred_dept_id = Department.query.first().id
        form = AddImageForm()
        return render_template(
            "submit_image.html", form=form, preferred_dept_id=preferred_dept_id
        )


@main.route(
    "/download/department/<int:department_id>/officers", methods=[HTTPMethod.GET]
)
@limiter.limit("5/minute")
def download_dept_officers_csv(department_id):
    officers = (
        db.session.query(Officer)
        .options(joinedload(Officer.assignments_lazy).joinedload(Assignment.job))
        .options(joinedload(Officer.salaries))
        .filter_by(department_id=department_id)
    )

    field_names = [
        "id",
        "unique identifier",
        "last name",
        "first name",
        "middle initial",
        "suffix",
        "gender",
        "race",
        "birth year",
        "employment date",
        "badge number",
        "job title",
        "most recent salary",
    ]
    return downloads.make_downloadable_csv(
        officers, department_id, "Officers", field_names, downloads.officer_record_maker
    )


@main.route(
    "/download/department/<int:department_id>/assignments", methods=[HTTPMethod.GET]
)
@limiter.limit("5/minute")
def download_dept_assignments_csv(department_id):
    assignments = (
        db.session.query(Assignment)
        .join(Assignment.baseofficer)
        .filter(Officer.department_id == department_id)
        .options(contains_eager(Assignment.baseofficer))
        .options(joinedload(Assignment.unit))
        .options(joinedload(Assignment.job))
    )

    field_names = [
        "id",
        "officer id",
        "officer unique identifier",
        "badge number",
        "job title",
        "start date",
        "end date",
        "unit id",
        "unit description",
    ]
    return downloads.make_downloadable_csv(
        assignments,
        department_id,
        "Assignments",
        field_names,
        downloads.assignment_record_maker,
    )


@main.route(
    "/download/department/<int:department_id>/incidents", methods=[HTTPMethod.GET]
)
@limiter.limit("5/minute")
def download_incidents_csv(department_id):
    incidents = Incident.query.filter_by(department_id=department_id).all()
    field_names = [
        "id",
        "report_num",
        "date",
        "time",
        "description",
        "location",
        "licenses",
        "links",
        "officers",
    ]
    return downloads.make_downloadable_csv(
        incidents,
        department_id,
        "Incidents",
        field_names,
        downloads.incidents_record_maker,
    )


@main.route(
    "/download/department/<int:department_id>/salaries", methods=[HTTPMethod.GET]
)
@limiter.limit("5/minute")
def download_dept_salaries_csv(department_id):
    salaries = (
        db.session.query(Salary)
        .join(Salary.officer)
        .filter(Officer.department_id == department_id)
        .options(contains_eager(Salary.officer))
    )

    field_names = [
        "id",
        "officer id",
        "first name",
        "last name",
        "salary",
        "overtime_pay",
        "year",
        "is_fiscal_year",
    ]
    return downloads.make_downloadable_csv(
        salaries, department_id, "Salaries", field_names, downloads.salary_record_maker
    )


@main.route("/download/department/<int:department_id>/links", methods=[HTTPMethod.GET])
@limiter.limit("5/minute")
def download_dept_links_csv(department_id):
    links = (
        db.session.query(Link)
        .join(Link.officers)
        .filter(Officer.department_id == department_id)
        .options(contains_eager(Link.officers))
    )

    field_names = [
        "id",
        "title",
        "url",
        "link_type",
        "description",
        "author",
        "officers",
        "incidents",
    ]
    return downloads.make_downloadable_csv(
        links, department_id, "Links", field_names, downloads.links_record_maker
    )


@main.route(
    "/download/department/<int:department_id>/descriptions", methods=[HTTPMethod.GET]
)
@limiter.limit("5/minute")
def download_dept_descriptions_csv(department_id):
    notes = (
        db.session.query(Description)
        .join(Description.officer)
        .filter(Officer.department_id == department_id)
        .options(contains_eager(Description.officer))
    )

    field_names = [
        "id",
        "text_contents",
        "creator_id",
        "officer_id",
        "date_created",
        "date_updated",
    ]
    return downloads.make_downloadable_csv(
        notes, department_id, "Notes", field_names, downloads.descriptions_record_maker
    )


@sitemap_include
@main.route("/download/all", methods=[HTTPMethod.GET])
def all_data():
    departments = Department.query.filter(Department.officers.any())
    return render_template("all_depts.html", departments=departments)


@main.route(
    "/submit_officer_images/officer/<int:officer_id>",
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)
@login_required
@ac_or_admin_required
def submit_officer_images(officer_id):
    officer = Officer.query.get_or_404(officer_id)
    return render_template("submit_officer_image.html", officer=officer)


@main.route("/upload/department/<int:department_id>", methods=[HTTPMethod.POST])
@main.route(
    "/upload/department/<int:department_id>/officer/<int:officer_id>",
    methods=[HTTPMethod.POST],
)
@limiter.limit("250/minute")
def upload(department_id, officer_id=None):
    if officer_id:
        officer = Officer.query.filter_by(id=officer_id).first()
        if not officer:
            return jsonify(error="This officer does not exist."), HTTPStatus.NOT_FOUND
        if not (
            current_user.is_administrator
            or (
                current_user.is_area_coordinator
                and officer.department_id == current_user.ac_department_id
            )
        ):
            return (
                jsonify(
                    error="You are not authorized to upload photos of this officer."
                ),
                HTTPStatus.FORBIDDEN,
            )
    file_to_upload = request.files["file"]
    if not allowed_file(file_to_upload.filename):
        return (
            jsonify(error="File type not allowed!"),
            HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
        )

    try:
        image = upload_image_to_s3_and_store_in_db(
            file_to_upload, current_user.get_id(), department_id=department_id
        )
    except ValueError:
        # Raised if MIME type not allowed
        return jsonify(error="Invalid data type!"), HTTPStatus.UNSUPPORTED_MEDIA_TYPE

    if image:
        db.session.add(image)
        if officer_id:
            image.is_tagged = True
            image.contains_cops = True
            face = Face(
                officer_id=officer_id,
                # Assuming photos uploaded with an officer ID are already cropped, so we set both images to the uploaded one
                img_id=image.id,
                original_image_id=image.id,
                user_id=current_user.get_id(),
            )
            db.session.add(face)
            db.session.commit()
        return jsonify(success="Success!"), HTTPStatus.OK
    else:
        return (
            jsonify(error="Server error encountered. Try again later."),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )


@sitemap_include
@main.route("/about")
def about_oo():
    return render_template("about.html")


@sitemap_include
@main.route("/privacy")
def privacy_oo():
    return render_template("privacy.html")


@main.route("/shutdown")  # pragma: no cover
def server_shutdown():  # pragma: no cover
    if not current_app.testing:
        abort(HTTPStatus.NOT_FOUND)
    shutdown = request.environ.get("werkzeug.server.shutdown")
    if not shutdown:
        abort(HTTPStatus.INTERNAL_SERVER_ERROR)
    shutdown()
    return "Shutting down..."


class IncidentApi(ModelView):
    model = Incident
    model_name = "incident"
    order_by = "date"
    descending = True
    form = IncidentForm
    create_function = create_incident
    department_check = True

    def get(self, obj_id):
        if obj_id:
            # Single-item view
            return super(IncidentApi, self).get(obj_id)

        # List view
        if request.args.get("page"):
            page = int(request.args.get("page"))
        else:
            page = 1

        form = IncidentListForm()
        incidents = self.model.query

        dept = None
        if department_id := request.args.get("department_id"):
            dept = Department.query.get_or_404(department_id)
            form.department_id.data = department_id
            incidents = incidents.filter_by(department_id=department_id)

        if report_number := request.args.get("report_number"):
            form.report_number.data = report_number
            incidents = incidents.filter(
                Incident.report_number.contains(report_number.strip())
            )

        if occurred_before := request.args.get("occurred_before"):
            before_date = datetime.datetime.strptime(occurred_before, "%Y-%m-%d").date()
            form.occurred_before.data = before_date
            incidents = incidents.filter(self.model.date < before_date)

        if occurred_after := request.args.get("occurred_after"):
            after_date = datetime.datetime.strptime(occurred_after, "%Y-%m-%d").date()
            form.occurred_after.data = after_date
            incidents = incidents.filter(self.model.date > after_date)

        incidents = incidents.order_by(
            getattr(self.model, self.order_by).desc()
        ).paginate(page=page, per_page=self.per_page, error_out=False)

        url = "main.{}_api".format(self.model_name)
        next_url = url_for(
            url,
            page=incidents.next_num,
            department_id=department_id,
            report_number=report_number,
            occurred_after=occurred_after,
            occurred_before=occurred_before,
        )
        prev_url = url_for(
            url,
            page=incidents.prev_num,
            department_id=department_id,
            report_number=report_number,
            occurred_after=occurred_after,
            occurred_before=occurred_before,
        )

        return render_template(
            "{}_list.html".format(self.model_name),
            form=form,
            incidents=incidents,
            url=url,
            next_url=next_url,
            prev_url=prev_url,
            department=dept,
        )

    def get_new_form(self):
        form = self.form()
        if request.args.get("officer_id"):
            form.officers[0].oo_id.data = request.args.get("officer_id")

        for link in form.links:
            link.creator_id.data = current_user.id
        return form

    def get_edit_form(self, obj):
        form = super(IncidentApi, self).get_edit_form(obj=obj)

        no_license_plates = len(obj.license_plates)
        no_links = len(obj.links)
        no_officers = len(obj.officers)
        for link in form.links:
            if link.creator_id.data:
                continue
            else:
                link.creator_id.data = current_user.id

        for officer_idx, officer in enumerate(obj.officers):
            form.officers[officer_idx].oo_id.data = officer.id

        # set the form to have fields for all the current model's items
        form.license_plates.min_entries = no_license_plates
        form.links.min_entries = no_links
        form.officers.min_entries = no_officers
        if not form.date_field.data and obj.date:
            form.date_field.data = obj.date
        if not form.time_field.data and obj.time:
            form.time_field.data = obj.time
        return form

    def populate_obj(self, form, obj):
        # remove all fields not directly on the Incident model
        # use utils to add them to the current object
        address = form.data.pop("address")
        del form.address
        if address["city"]:
            new_address, _ = get_or_create(db.session, Location, **address)
            obj.address = new_address
        else:
            obj.address = None

        links = form.data.pop("links")
        del form.links
        if links and links[0]["url"]:
            replace_list(links, obj, "links", Link, db)

        officers = form.data.pop("officers")
        del form.officers
        if officers:
            for officer in officers:
                if officer["oo_id"]:
                    try:
                        of = Officer.query.filter_by(id=int(officer["oo_id"])).first()
                    # Sometimes we get a string in officer["oo_id"], this parses it
                    except ValueError:
                        our_id = officer["oo_id"].split('value="')[1][:-2]
                        of = Officer.query.filter_by(id=int(our_id)).first()
                    if of:
                        obj.officers.append(of)

        license_plates = form.data.pop("license_plates")
        del form.license_plates
        if license_plates and license_plates[0]["number"]:
            replace_list(license_plates, obj, "license_plates", LicensePlate, db)

        obj.date = form.date_field.data
        if form.time_field.raw_data and form.time_field.raw_data != [""]:
            obj.time = form.time_field.data
        else:
            obj.time = None
        super(IncidentApi, self).populate_obj(form, obj)


incident_view = IncidentApi.as_view("incident_api")
main.add_url_rule(
    "/incidents/",
    defaults={"obj_id": None},
    view_func=incident_view,
    methods=[HTTPMethod.GET],
)
main.add_url_rule(
    "/incidents/new",
    view_func=incident_view,
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)
main.add_url_rule(
    "/incidents/<int:obj_id>", view_func=incident_view, methods=[HTTPMethod.GET]
)
main.add_url_rule(
    "/incidents/<int:obj_id>/edit",
    view_func=incident_view,
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)
main.add_url_rule(
    "/incidents/<int:obj_id>/delete",
    view_func=incident_view,
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)


@sitemap.register_generator
def sitemap_incidents():
    for incident in Incident.query.all():
        yield "main.incident_api", {"obj_id": incident.id}


class TextApi(ModelView):
    order_by = "date_created"
    descending = True
    department_check = True
    form = TextForm

    def get_new_form(self):
        form = self.form()
        form.officer_id.data = self.officer_id
        return form

    def get_redirect_url(self, *args, **kwargs):
        return redirect(url_for("main.officer_profile", officer_id=self.officer_id))

    def get_post_delete_url(self, *args, **kwargs):
        return self.get_redirect_url()

    def get_department_id(self, obj):
        return self.department_id

    def get_edit_form(self, obj):
        form = EditTextForm(obj=obj)
        return form

    def dispatch_request(self, *args, **kwargs):
        if "officer_id" in kwargs:
            officer = Officer.query.get_or_404(kwargs["officer_id"])
            self.officer_id = kwargs.pop("officer_id")
            self.department_id = officer.department_id
        return super(TextApi, self).dispatch_request(*args, **kwargs)


class NoteApi(TextApi):
    model = Note
    model_name = "note"
    form = TextForm
    create_function = create_note

    def dispatch_request(self, *args, **kwargs):
        return super(NoteApi, self).dispatch_request(*args, **kwargs)


class DescriptionApi(TextApi):
    model = Description
    model_name = "description"
    form = TextForm
    create_function = create_description

    def dispatch_request(self, *args, **kwargs):
        return super(DescriptionApi, self).dispatch_request(*args, **kwargs)


note_view = NoteApi.as_view("note_api")
main.add_url_rule(
    "/officer/<int:officer_id>/note/new",
    view_func=note_view,
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)
main.add_url_rule(
    "/officer/<int:officer_id>/note/<int:obj_id>",
    view_func=note_view,
    methods=[HTTPMethod.GET],
)
main.add_url_rule(
    "/officer/<int:officer_id>/note/<int:obj_id>/edit",
    view_func=note_view,
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)
main.add_url_rule(
    "/officer/<int:officer_id>/note/<int:obj_id>/delete",
    view_func=note_view,
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)

description_view = DescriptionApi.as_view("description_api")
main.add_url_rule(
    "/officer/<int:officer_id>/description/new",
    view_func=description_view,
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)
main.add_url_rule(
    "/officer/<int:officer_id>/description/<int:obj_id>",
    view_func=description_view,
    methods=[HTTPMethod.GET],
)
main.add_url_rule(
    "/officer/<int:officer_id>/description/<int:obj_id>/edit",
    view_func=description_view,
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)
main.add_url_rule(
    "/officer/<int:officer_id>/description/<int:obj_id>/delete",
    view_func=description_view,
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)


class OfficerLinkApi(ModelView):
    """This API only applies to links attached to officer profiles, not links attached to incidents"""

    model = Link
    model_name = "link"
    form = OfficerLinkForm
    department_check = True

    @property
    def officer(self):
        if not hasattr(self, "_officer"):
            self._officer = (
                db.session.query(Officer).filter_by(id=self.officer_id).one()
            )
        return self._officer

    @login_required
    @ac_or_admin_required
    def new(self, form=None):
        if (
            not current_user.is_administrator
            and current_user.ac_department_id != self.officer.department_id
        ):
            abort(HTTPStatus.FORBIDDEN)
        if not form:
            form = self.get_new_form()
            if hasattr(form, "creator_id") and not form.creator_id.data:
                form.creator_id.data = current_user.get_id()

        if form.validate_on_submit():
            link = Link(
                title=form.title.data,
                url=form.url.data,
                link_type=form.link_type.data,
                description=form.description.data,
                author=form.author.data,
                creator_id=form.creator_id.data,
            )
            self.officer.links.append(link)
            db.session.add(link)
            db.session.commit()
            flash("{} created!".format(self.model_name))
            return self.get_redirect_url(obj_id=link.id)

        return render_template("{}_new.html".format(self.model_name), form=form)

    @login_required
    @ac_or_admin_required
    def delete(self, obj_id):
        obj = self.model.query.get_or_404(obj_id)
        if (
            not current_user.is_administrator
            and current_user.ac_department_id != self.get_department_id(obj)
        ):
            abort(HTTPStatus.FORBIDDEN)

        if request.method == HTTPMethod.POST:
            db.session.delete(obj)
            db.session.commit()
            flash("{} successfully deleted!".format(self.model_name))
            return self.get_post_delete_url()

        return render_template(
            "{}_delete.html".format(self.model_name),
            obj=obj,
            officer_id=self.officer_id,
        )

    def get_new_form(self):
        form = self.form()
        form.officer_id.data = self.officer_id
        return form

    def get_edit_form(self, obj):
        form = self.form(obj=obj)
        form.officer_id.data = self.officer_id
        return form

    def get_redirect_url(self, *args, **kwargs):
        return redirect(url_for("main.officer_profile", officer_id=self.officer_id))

    def get_post_delete_url(self, *args, **kwargs):
        return self.get_redirect_url()

    def get_department_id(self, obj):
        return self.officer.department_id

    def dispatch_request(self, *args, **kwargs):
        if "officer_id" in kwargs:
            officer = Officer.query.get_or_404(kwargs["officer_id"])
            self.officer_id = kwargs.pop("officer_id")
            self.department_id = officer.department_id
        return super(OfficerLinkApi, self).dispatch_request(*args, **kwargs)


main.add_url_rule(
    "/officer/<int:officer_id>/link/new",
    view_func=OfficerLinkApi.as_view("link_api_new"),
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)
main.add_url_rule(
    "/officer/<int:officer_id>/link/<int:obj_id>/edit",
    view_func=OfficerLinkApi.as_view("link_api_edit"),
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)
main.add_url_rule(
    "/officer/<int:officer_id>/link/<int:obj_id>/delete",
    view_func=OfficerLinkApi.as_view("link_api_delete"),
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)
