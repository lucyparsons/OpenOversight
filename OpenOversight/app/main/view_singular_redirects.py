from http import HTTPMethod, HTTPStatus

from flask import flash, redirect, url_for
from flask_login import login_required

from OpenOversight.app.main import main
from OpenOversight.app.utils.auth import ac_or_admin_required
from OpenOversight.app.utils.constants import FLASH_MSG_PERMANENT_REDIRECT


@main.route("/label", methods=[HTTPMethod.GET, HTTPMethod.POST])
def redirect_get_started_labeling():
    flash(FLASH_MSG_PERMANENT_REDIRECT)
    return redirect(
        url_for("main.get_started_labeling"), code=HTTPStatus.PERMANENT_REDIRECT
    )


@main.route(
    "/sort/department/<int:department_id>", methods=[HTTPMethod.GET, HTTPMethod.POST]
)
@login_required
def redirect_sort_images(department_id: int):
    flash(FLASH_MSG_PERMANENT_REDIRECT)
    return redirect(
        url_for("main.sort_images", department_id=department_id),
        code=HTTPStatus.PERMANENT_REDIRECT,
    )


@main.route("/officer/<int:officer_id>", methods=[HTTPMethod.GET, HTTPMethod.POST])
def redirect_officer_profile(officer_id: int):
    flash(FLASH_MSG_PERMANENT_REDIRECT)
    return redirect(
        url_for("main.officer_profile", officer_id=officer_id),
        code=HTTPStatus.PERMANENT_REDIRECT,
    )


@main.route(
    "/officer/<int:officer_id>/assignment/new",
    methods=[HTTPMethod.GET, HTTPMethod.POST],
)
@ac_or_admin_required
def redirect_add_assignment(officer_id: int):
    return redirect(
        url_for("main.add_assignment", officer_id=officer_id),
        code=HTTPStatus.PERMANENT_REDIRECT,
    )
