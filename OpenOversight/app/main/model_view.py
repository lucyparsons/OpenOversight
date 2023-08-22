import datetime
from http import HTTPMethod
from typing import Callable, Union

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask.views import MethodView
from flask_login import current_user, login_required
from flask_sqlalchemy.model import DefaultMeta
from flask_wtf import Form

from OpenOversight.app.models.database import (
    Department,
    Incident,
    Link,
    Note,
    Officer,
    db,
)
from OpenOversight.app.utils.auth import ac_or_admin_required
from OpenOversight.app.utils.constants import (
    KEY_DEPT_ALL_INCIDENTS,
    KEY_DEPT_ALL_LINKS,
    KEY_DEPT_ALL_NOTES,
    KEY_DEPT_TOTAL_INCIDENTS,
)
from OpenOversight.app.utils.db import add_department_query
from OpenOversight.app.utils.forms import set_dynamic_default


class ModelView(MethodView):
    model: DefaultMeta = None
    model_name: str = ""
    per_page = 20
    order_by: str = ""  # this should be a field on the model
    descending = False  # used for order_by
    form: Form = None
    create_function: Union[str, Callable] = ""
    department_check = False

    def get(self, obj_id):
        if obj_id is None:
            page = int(request.args.get("page", 1))

            if self.order_by:
                if not self.descending:
                    objects = self.model.query.order_by(
                        getattr(self.model, self.order_by)
                    ).paginate(page=page, per_page=self.per_page, error_out=False)
                else:
                    objects = self.model.query.order_by(
                        getattr(self.model, self.order_by).desc()
                    ).paginate(page=page, per_page=self.per_page, error_out=False)
            else:
                objects = self.model.query.paginate(
                    page=page, per_page=self.per_page, error_out=False
                )

            return render_template(
                f"{self.model_name}_list.html",
                objects=objects,
                url=f"main.{self.model_name}_api",
            )
        else:
            obj = self.model.query.get_or_404(obj_id)
            return render_template(
                f"{self.model_name}_detail.html",
                obj=obj,
                current_user=current_user,
            )

    @login_required
    @ac_or_admin_required
    def new(self, form=None):
        if not form:
            form = self.get_new_form()
            if hasattr(form, "department"):
                add_department_query(form, current_user)
                if getattr(current_user, "dept_pref_rel", None):
                    set_dynamic_default(form.department, current_user.dept_pref_rel)

        if form.validate_on_submit():
            new_obj = self.create_function(form, current_user)
            if hasattr(new_obj, "created_by"):
                new_obj.created_by = current_user.get_id()
            if hasattr(new_obj, "last_updated_by"):
                new_obj.last_updated_by = current_user.get_id()
            db.session.add(new_obj)
            db.session.commit()

            match self.model.__name__:
                case Incident.__name__:
                    Department(id=new_obj.department_id).remove_database_cache_entries(
                        [KEY_DEPT_TOTAL_INCIDENTS, KEY_DEPT_ALL_INCIDENTS],
                    )
                case Note.__name__:
                    officer = Officer.query.filter_by(
                        department_id=new_obj.officer_id
                    ).first()
                    if officer:
                        Department(
                            id=officer.department_id
                        ).remove_database_cache_entries(
                            [KEY_DEPT_ALL_NOTES],
                        )
            flash(f"{self.model_name} created!")
            return self.get_redirect_url(obj_id=new_obj.id)
        else:
            current_app.logger.info(form.errors)

        return render_template(f"{self.model_name}_new.html", form=form)

    @login_required
    @ac_or_admin_required
    def edit(self, obj_id, form=None):
        obj = self.model.query.get_or_404(obj_id)
        if self.department_check:
            if (
                not current_user.is_administrator
                and current_user.ac_department_id != self.get_department_id(obj)
            ):
                abort(403)

        if not form:
            form = self.get_edit_form(obj)

        if hasattr(form, "department"):
            add_department_query(form, current_user)

        if form.validate_on_submit():
            self.populate_obj(form, obj)
            match self.model.__name__:
                case Incident.__name__:
                    Department(id=obj.department_id).remove_database_cache_entries(
                        [KEY_DEPT_ALL_INCIDENTS],
                    )
                case Note.__name__:
                    officer = Officer.query.filter_by(
                        department_id=obj.officer_id
                    ).first()
                    if officer:
                        Department(
                            id=officer.department_id
                        ).remove_database_cache_entries(
                            [KEY_DEPT_ALL_NOTES],
                        )
                case Link.__name__:
                    officer = Officer.query.filter_by(id=obj.officer_id).first()
                    if officer:
                        Department(
                            id=officer.department_id
                        ).remove_database_cache_entries(
                            [KEY_DEPT_ALL_LINKS],
                        )
            flash(f"{self.model_name} successfully updated!")
            return self.get_redirect_url(obj_id=obj_id)

        return render_template(f"{self.model_name}_edit.html", obj=obj, form=form)

    @login_required
    @ac_or_admin_required
    def delete(self, obj_id):
        obj = self.model.query.get_or_404(obj_id)
        if self.department_check:
            if (
                not current_user.is_administrator
                and current_user.ac_department_id != self.get_department_id(obj)
            ):
                abort(403)

        if request.method == HTTPMethod.POST:
            db.session.delete(obj)
            db.session.commit()
            match self.model.__name__:
                case Incident.__name__:
                    Department(id=obj.department_id).remove_database_cache_entries(
                        [KEY_DEPT_TOTAL_INCIDENTS, KEY_DEPT_ALL_INCIDENTS],
                    )
                case Note.__name__:
                    officer = Officer.query.filter_by(
                        department_id=obj.officer_id
                    ).first()
                    if officer:
                        Department(
                            id=officer.department_id
                        ).remove_database_cache_entries(
                            [KEY_DEPT_ALL_NOTES],
                        )
            flash(f"{self.model_name} successfully deleted!")
            return self.get_post_delete_url()

        return render_template(f"{self.model_name}_delete.html", obj=obj)

    def get_edit_form(self, obj):
        form = self.form(obj=obj)
        return form

    def get_new_form(self):
        return self.form()

    def get_redirect_url(self, *args, **kwargs):
        # returns user to the show view
        return redirect(
            url_for(
                f"main.{self.model_name}_api",
                obj_id=kwargs["obj_id"],
                _method=HTTPMethod.GET,
            )
        )

    def get_post_delete_url(self, *args, **kwargs):
        # returns user to the list view
        return redirect(url_for(f"main.{self.model_name}_api"))

    def get_department_id(self, obj):
        return obj.department_id

    def populate_obj(self, form, obj):
        form.populate_obj(obj)

        # if the object doesn't have a creator id set it to current user
        if hasattr(obj, "created_by") and not getattr(obj, "created_by"):
            obj.created_by = current_user.get_id()
        # if the object keeps track of who updated it last, set to current user
        if hasattr(obj, "last_updated_at"):
            obj.last_updated_at = datetime.datetime.now()
            obj.last_updated_by = current_user.get_id()

        db.session.add(obj)
        db.session.commit()

    def create_obj(self, form):
        self.model(**form.data)

    def dispatch_request(self, *args, **kwargs):
        # isolate the method at the end of the url
        end_of_url = request.url.split("/")[-1].split("?")[0]
        endings = ["edit", "new", "delete"]
        meth = None
        for ending in endings:
            if end_of_url == ending:
                meth = getattr(self, ending, None)
        if not meth:
            if request.method == HTTPMethod.GET:
                meth = getattr(self, "get", None)
            else:
                assert meth is not None, f"Unimplemented method {request.method!r}"
        return meth(*args, **kwargs)
