from http import HTTPMethod, HTTPStatus

from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from OpenOversight.app import sitemap
from OpenOversight.app.auth import auth
from OpenOversight.app.auth.forms import (
    ChangeDefaultDepartmentForm,
    ChangeEmailForm,
    ChangePasswordForm,
    EditUserForm,
    LoginForm,
    PasswordResetForm,
    PasswordResetRequestForm,
    RegistrationForm,
)
from OpenOversight.app.email_client import EmailClient
from OpenOversight.app.models.database import User, db
from OpenOversight.app.models.emails import (
    AdministratorApprovalEmail,
    ChangeEmailAddressEmail,
    ChangePasswordEmail,
    ConfirmAccountEmail,
    ConfirmedUserEmail,
    ResetPasswordEmail,
)
from OpenOversight.app.utils.auth import admin_required
from OpenOversight.app.utils.forms import set_dynamic_default
from OpenOversight.app.utils.general import validate_redirect_url


js_loads = ["js/zxcvbn.js", "js/password.js"]
sitemap_endpoints = []


def sitemap_include(view):
    sitemap_endpoints.append(view.__name__)
    return view


@sitemap.register_generator
def static_routes():
    for endpoint in sitemap_endpoints:
        yield "auth." + endpoint, {}


@auth.before_app_request
def before_request():
    if (
        current_user.is_authenticated
        and not current_user.confirmed
        and request.endpoint
        and request.endpoint[:5] != "auth."
        and request.endpoint != "static"
    ):
        return redirect(url_for("auth.unconfirmed"))


@auth.route("/unconfirmed")
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for("main.index"))
    if current_app.config["APPROVE_REGISTRATIONS"]:
        return render_template("auth/unapproved.html")
    else:
        return render_template("auth/unconfirmed.html")


@sitemap_include
@auth.route("/login", methods=[HTTPMethod.GET, HTTPMethod.POST])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.by_email(form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            if user.is_active:
                login_user(user, form.remember_me.data)
                next_url = validate_redirect_url(session.get("next"))
                return redirect(next_url or url_for("main.index"))
            else:
                flash("User has been disabled.")
        else:
            flash("Invalid username or password.")
    else:
        current_app.logger.info(form.errors)
    return render_template("auth/login.html", form=form)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("main.index"))


@sitemap_include
@auth.route("/register", methods=[HTTPMethod.GET, HTTPMethod.POST])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            username=form.username.data,
            password=form.password.data,
            approved=False if current_app.config["APPROVE_REGISTRATIONS"] else True,
        )
        db.session.add(user)
        db.session.commit()
        if current_app.config["APPROVE_REGISTRATIONS"]:
            admins = User.query.filter_by(is_administrator=True).all()
            for admin in admins:
                EmailClient.send_email(
                    AdministratorApprovalEmail(admin.email, user=user, admin=admin)
                )
            flash(
                "Once an administrator approves your registration, you will "
                "receive a confirmation email to activate your account."
            )
        else:
            token = user.generate_confirmation_token()
            EmailClient.send_email(
                ConfirmAccountEmail(user.email, user=user, token=token)
            )
            flash("A confirmation email has been sent to you.")
        return redirect(url_for("auth.login"))
    else:
        current_app.logger.info(form.errors)
    return render_template("auth/register.html", form=form, jsloads=js_loads)


@auth.route("/confirm/<token>", methods=[HTTPMethod.GET])
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for("main.index"))
    if current_user.confirm(token):
        admins = User.query.filter_by(is_administrator=True).all()
        for admin in admins:
            EmailClient.send_email(
                ConfirmedUserEmail(admin.email, user=current_user, admin=admin)
            )
        flash("You have confirmed your account. Thanks!")
    else:
        flash("The confirmation link is invalid or has expired.")
    return redirect(url_for("main.index"))


@auth.route("/confirm")
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    EmailClient.send_email(
        ConfirmAccountEmail(current_user.email, user=current_user, token=token)
    )
    flash("A new confirmation email has been sent to you.")
    return redirect(url_for("main.index"))


@auth.route("/change-password", methods=[HTTPMethod.GET, HTTPMethod.POST])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash("Your password has been updated. Please log in again.")
            EmailClient.send_email(
                ChangePasswordEmail(current_user.email, user=current_user)
            )
            return redirect(url_for("main.index"))
        else:
            flash("Invalid password.")
    else:
        current_app.logger.info(form.errors)
    return render_template("auth/change_password.html", form=form, jsloads=js_loads)


@auth.route("/reset", methods=[HTTPMethod.GET, HTTPMethod.POST])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for("main.index"))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.by_email(form.email.data).first()
        if user:
            token = user.generate_reset_token()
            EmailClient.send_email(
                ResetPasswordEmail(user.email, user=user, token=token)
            )
        flash("An email with instructions to reset your password has been sent to you.")
        return redirect(url_for("auth.login"))
    else:
        current_app.logger.info(form.errors)
    return render_template("auth/reset_password.html", form=form)


@auth.route("/reset/<token>", methods=[HTTPMethod.GET, HTTPMethod.POST])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for("main.index"))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.by_email(form.email.data).first()
        if user is None:
            return redirect(url_for("main.index"))
        if user.reset_password(token, form.password.data):
            flash("Your password has been updated. Please log in again.")
            return redirect(url_for("auth.login"))
        else:
            return redirect(url_for("main.index"))
    else:
        current_app.logger.info(form.errors)
    return render_template("auth/reset_password.html", form=form)


@auth.route("/change-email", methods=[HTTPMethod.GET, HTTPMethod.POST])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            EmailClient.send_email(
                ChangeEmailAddressEmail(new_email, user=current_user, token=token)
            )
            flash(
                "An email with instructions to confirm your new email "
                "address has been sent to you."
            )
            return redirect(url_for("main.index"))
        else:
            flash("Invalid email or password.")
    else:
        current_app.logger.info(form.errors)
    return render_template("auth/change_email.html", form=form)


@auth.route("/change-email/<token>")
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash("Your email address has been updated. Please log in again.")
    else:
        flash("Invalid request.")
    return redirect(url_for("main.index"))


@auth.route("/change-dept/", methods=[HTTPMethod.GET, HTTPMethod.POST])
@login_required
def change_dept():
    form = ChangeDefaultDepartmentForm()
    set_dynamic_default(form.dept_pref, current_user.dept_pref_rel)

    if form.validate_on_submit():
        try:
            current_user.dept_pref = form.dept_pref.data.id
        except AttributeError:
            current_user.dept_pref = None
        db.session.add(current_user)
        db.session.commit()
        flash("Updated!")
        return redirect(url_for("main.index"))
    else:
        current_app.logger.info(form.errors)
    return render_template("auth/change_dept_pref.html", form=form)


@auth.route("/users/", methods=[HTTPMethod.GET])
@admin_required
def get_users():
    page = int(request.args.get("page", 1))
    users = User.query.order_by(User.username).paginate(
        page=page, per_page=current_app.config["USERS_PER_PAGE"], error_out=False
    )

    return render_template("auth/users.html", objects=users)


@auth.route("/users/<int:user_id>", methods=[HTTPMethod.GET, HTTPMethod.POST])
@admin_required
def edit_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return render_template("404.html"), HTTPStatus.NOT_FOUND

    if request.method == HTTPMethod.GET:
        form = EditUserForm(obj=user)
        return render_template("auth/user.html", user=user, form=form)
    elif request.method == HTTPMethod.POST:
        form = EditUserForm()
        if form.delete.data:
            # forward to confirm delete
            return redirect(url_for("auth.delete_user", user_id=user.id))
        elif form.resend.data:
            return admin_resend_confirmation(user)
        elif form.submit.data:
            if form.validate_on_submit():
                # prevent user from removing own admin rights (or disabling account)
                if user.id == current_user.id:
                    flash("You cannot edit your own account!")
                    form = EditUserForm(obj=user)
                    return render_template("auth/user.html", user=user, form=form)
                already_approved = user.approved
                form.populate_obj(user)
                db.session.add(user)
                db.session.commit()

                # automatically send a confirmation email when approving an
                # unconfirmed user
                if (
                    current_app.config["APPROVE_REGISTRATIONS"]
                    and not already_approved
                    and user.approved
                    and not user.confirmed
                ):
                    admin_resend_confirmation(user)

                flash(f"{user.username} has been updated!")

                return redirect(url_for("auth.edit_user", user_id=user.id))
            else:
                flash("Invalid entry")
                return render_template("auth/user.html", user=user, form=form)


@auth.route("/users/<int:user_id>/delete", methods=[HTTPMethod.GET, HTTPMethod.POST])
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user or user.is_administrator:
        return render_template("403.html"), HTTPStatus.FORBIDDEN
    if request.method == HTTPMethod.POST:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        flash(f"User {username} has been deleted!")
        return redirect(url_for("auth.get_users"))

    return render_template("auth/user_delete.html", user=user)


def admin_resend_confirmation(user):
    if user.confirmed:
        flash(f"User {user.username} is already confirmed.")
    else:
        token = user.generate_confirmation_token()
        EmailClient.send_email(ConfirmAccountEmail(user.email, user=user, token=token))
        flash(f"A new confirmation email has been sent to {user.email}.")
    return redirect(url_for("auth.get_users"))
