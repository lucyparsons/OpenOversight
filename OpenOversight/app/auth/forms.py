from flask_wtf import FlaskForm as Form
from wtforms import (
    BooleanField,
    PasswordField,
    StringField,
    SubmitField,
    ValidationError,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp
from wtforms_sqlalchemy.fields import QuerySelectField

from OpenOversight.app.models.database import User
from OpenOversight.app.utils.db import dept_choices


class LoginForm(Form):
    email = StringField("Email", validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Keep me logged in")
    submit = SubmitField("Log In")


class RegistrationForm(Form):
    email = StringField("Email", validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(6, 64),
            Regexp(
                "^[A-Za-z][A-Za-z0-9_.]*$",
                0,
                "Usernames must have only letters, " "numbers, dots or underscores",
            ),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(8, 64),
            EqualTo("password2", message="Passwords must match."),
        ],
    )
    password2 = PasswordField("Confirm password", validators=[DataRequired()])
    submit = SubmitField("Register")

    def validate_email(self, field):
        if User.by_email(field.data).first():
            raise ValidationError("Email already registered.")

    def validate_username(self, field):
        if User.by_username(field.data).first():
            raise ValidationError("Username already in use.")


class ChangePasswordForm(Form):
    old_password = PasswordField("Old password", validators=[DataRequired()])
    password = PasswordField(
        "New password",
        validators=[
            DataRequired(),
            Length(8, 64),
            EqualTo("password2", message="Passwords must match"),
        ],
    )
    password2 = PasswordField("Confirm new password", validators=[DataRequired()])
    submit = SubmitField("Update Password")


class PasswordResetRequestForm(Form):
    email = StringField("Email", validators=[DataRequired(), Length(1, 64), Email()])
    submit = SubmitField("Reset Password")


class PasswordResetForm(Form):
    email = StringField("Email", validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            EqualTo("password2", message="Passwords must match"),
        ],
    )
    password2 = PasswordField("Confirm password", validators=[DataRequired()])
    submit = SubmitField("Reset Password")

    def validate_email(self, field):
        if User.by_email(field.data).first() is None:
            raise ValidationError("Unknown email address.")


class ChangeEmailForm(Form):
    email = StringField(
        "New Email", validators=[DataRequired(), Length(1, 64), Email()]
    )
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Update Email Address")

    def validate_email(self, field):
        if User.by_email(field.data).first():
            raise ValidationError("Email already registered.")


class ChangeDefaultDepartmentForm(Form):
    dept_pref = QuerySelectField(
        "Default Department (Optional)",
        validators=[Optional()],
        query_factory=dept_choices,
        get_label="name",
        allow_blank=True,
    )
    submit = SubmitField("Update Default")


class EditUserForm(Form):
    is_area_coordinator = BooleanField(
        "Is area coordinator?", false_values={"False", "false", ""}
    )
    ac_department = QuerySelectField(
        "Department",
        validators=[Optional()],
        query_factory=dept_choices,
        get_label="name",
        allow_blank=True,
    )
    is_administrator = BooleanField(
        "Is administrator?", false_values={"False", "false", ""}
    )
    is_disabled = BooleanField("Disabled?", false_values={"False", "false", ""})
    approved = BooleanField("Approved?", false_values={"False", "false", ""})
    confirmed = BooleanField("Confirmed?", false_values={"False", "false", ""})
    submit = SubmitField(label="Update", false_values={"False", "false", ""})
    resend = SubmitField(label="Resend", false_values={"False", "false", ""})
    delete = SubmitField(label="Delete", false_values={"False", "false", ""})

    def validate(self, extra_validators=None):
        success = super(EditUserForm, self).validate(extra_validators=None)
        if self.is_area_coordinator.data and not self.ac_department.data:
            self.is_area_coordinator.errors = list(self.is_area_coordinator.errors)
            self.is_area_coordinator.errors.append(
                "Area coordinators must have a department"
            )
            success = False

        return success
