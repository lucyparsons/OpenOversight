from typing import Optional

from sqlalchemy import func

from ..models import Assignment, Department, Face, Image, Officer, Unit, User, db


def add_department_query(form, current_user):
    """Limits the departments available on forms for acs"""
    if not current_user.is_administrator:
        form.department.query = Department.query.filter_by(
            id=current_user.ac_department_id
        )


def add_unit_query(form, current_user):
    if not current_user.is_administrator:
        form.unit.query = Unit.query.filter_by(
            department_id=current_user.ac_department_id
        ).order_by(Unit.descrip.asc())
    else:
        form.unit.query = Unit.query.order_by(Unit.descrip.asc()).all()


def compute_leaderboard_stats(select_top=25):
    top_sorters = (
        db.session.query(User, func.count(Image.user_id))
        .select_from(Image)
        .join(User)
        .group_by(User)
        .order_by(func.count(Image.user_id).desc())
        .limit(select_top)
        .all()
    )
    top_taggers = (
        db.session.query(User, func.count(Face.user_id))
        .select_from(Face)
        .join(User)
        .group_by(User)
        .order_by(func.count(Face.user_id).desc())
        .limit(select_top)
        .all()
    )
    return top_sorters, top_taggers


def dept_choices():
    return db.session.query(Department).all()


def get_officer(department_id, star_no, first_name, last_name):
    """
    Return the first officer with the given name and badge combo in the department, if one exists.

    If star_no is None, just return the first officer with the given first and last name.
    """
    officers = Officer.query.filter_by(
        department_id=department_id, first_name=first_name, last_name=last_name
    ).all()

    if star_no is None:
        return officers[0]
    else:
        star_no = str(star_no)
        for assignment in Assignment.query.filter_by(star_no=star_no).all():
            if assignment.baseofficer in officers:
                return assignment.baseofficer
    return None


def unit_choices(department_id: Optional[int] = None):
    if department_id is not None:
        return (
            db.session.query(Unit)
            .filter_by(department_id=department_id)
            .order_by(Unit.descrip.asc())
            .all()
        )
    return db.session.query(Unit).order_by(Unit.descrip.asc()).all()
