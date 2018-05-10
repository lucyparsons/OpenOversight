# Routing and view tests
import pytest
import random
from flask import url_for, current_app
from urlparse import urlparse
from ..conftest import AC_DEPT
from OpenOversight.app.utils import dept_choices
from .route_helpers import login_user, login_admin, login_ac


from OpenOversight.app.auth.forms import (LoginForm, RegistrationForm,
                                          ChangePasswordForm, PasswordResetForm,
                                          PasswordResetRequestForm,
                                          ChangeEmailForm, ChangeDefaultDepartmentForm, EditUserForm)
from OpenOversight.app.models import (User, Face, Department, Unit, Officer, Image)

@pytest.mark.parametrize("route", [
    ('/incidents/'),
    ('/incidents/1')
])
def test_routes_ok(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == 200


@pytest.mark.parametrize("route", [
    ('incidents/1/edit'),
    ('incidents/new'),
    ('incidents/1/delete')
])
def test_route_login_required(route, client, mockdata):
    rv = client.get(route)
    assert rv.status_code == 302
