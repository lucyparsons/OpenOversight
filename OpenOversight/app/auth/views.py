from future.utils import iteritems

from flask import render_template, redirect, request, url_for, flash, current_app
from flask.views import MethodView
from flask_login import login_user, logout_user, login_required, \
    current_user
from . import auth
from ..models import User, db
from ..email import send_email
from .forms import LoginForm, RegistrationForm, ChangePasswordForm,\
    PasswordResetRequestForm, PasswordResetForm, ChangeEmailForm, ChangeDefaultDepartmentForm, \
    EditUserForm
from .utils import admin_required
from ..utils import set_dynamic_default


@auth.before_app_request
def before_request():
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.endpoint[:5] != 'auth.' \
            and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    jsloads = ['js/zxcvbn.js', 'js/password.js']
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account',
                   'auth/email/confirm', user=user, token=token)
        flash('A confirmation email has been sent to you.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form, jsloads=jsloads)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you.')
    return redirect(url_for('main.index'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    jsloads = ['js/zxcvbn.js', 'js/password.js']
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash('Your password has been updated.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password.')
    return render_template("auth/change_password.html", form=form, jsloads=jsloads)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, 'Reset Your Password',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
        flash('An email with instructions to reset your password has been '
              'sent to you.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.password.data):
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, 'Confirm your email address',
                       'auth/email/change_email',
                       user=current_user, token=token)
            flash('An email with instructions to confirm your new email '
                  'address has been sent to you.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password.')
    return render_template("auth/change_email.html", form=form)


@auth.route('/change-email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash('Your email address has been updated.')
    else:
        flash('Invalid request.')
    return redirect(url_for('main.index'))


@auth.route('/change-dept/', methods=['GET', 'POST'])
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
        flash('Updated!')
        return redirect(url_for('main.index'))
    return render_template('auth/change_dept_pref.html', form=form)


class UserAPI(MethodView):
    decorators = [admin_required]

    def get(self, user_id):
        if user_id is None:
            if request.args.get('page'):
                page = int(request.args.get('page'))
            else:
                page = 1
            USERS_PER_PAGE = int(current_app.config['USERS_PER_PAGE'])
            users = User.query.order_by(User.email) \
                .paginate(page, USERS_PER_PAGE, False)

            return render_template('auth/users.html', objects=users)
        else:
            user = User.query.get(user_id)

            if user:
                form = EditUserForm(
                    email=user.email,
                    is_area_coordinator=user.is_area_coordinator,
                    ac_department=user.ac_department,
                    is_administrator=user.is_administrator)
                return render_template('auth/user.html', user=user, form=form)
            else:
                return render_template('403.html'), 403

    def post(self, user_id):
        form = EditUserForm()
        user = User.query.get(user_id)

        if user and form.validate_on_submit():
            for field, data in iteritems(form.data):
                setattr(user, field, data)

            db.session.add(user)
            flash('{} has been updated!'.format(user.username))
            return redirect(url_for('auth.user_api'))
        elif not form.validate_on_submit():
            flash('Invalid entry')
            return render_template('auth/user.html', user=user, form=form)
        else:
            return render_template('403.html'), 403

    def delete(self, user_id):
        pass


user_view = UserAPI.as_view('user_api')
auth.add_url_rule(
    '/users/',
    defaults={'user_id': None},
    view_func=user_view,
    methods=['GET'])
auth.add_url_rule(
    '/users/<int:user_id>',
    view_func=user_view,
    methods=['GET', 'POST'])
