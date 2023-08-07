import datetime
from http import HTTPMethod

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask.views import MethodView
from flask_login import current_user, login_required

from OpenOversight.app.models.database import Department, db
from OpenOversight.app.models.database_cache import remove_department_cache_entry
from OpenOversight.app.utils.auth import ac_or_admin_required
from OpenOversight.app.utils.constants import KEY_DEPT_TOTAL_INCIDENTS
from OpenOversight.app.utils.db import add_department_query
from OpenOversight.app.utils.forms import set_dynamic_default


class ModelView(MethodView):
    model = None  # type: DefaultMeta
    model_name = ""
    per_page = 20
    order_by = ""  # this should be a field on the model
    descending = False  # used for order_by
    form = ""  # type: Form
    create_function = ""  # type: Union[str, Callable]
    department_check = False

    def get(self, obj_id):
        if obj_id is None:
            if request.args.get("page"):
                page = int(request.args.get("page"))
            else:
                page = 1

            if self.order_by:
                if not self.descending:
                    objects = self.model.query.order_by(
                        getattr(self.model, self.order_by)
                    ).paginate(page=page, per_page=self.per_page, error_out=False)
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
            if hasattr(form, "created_by") and not form.created_by.data:
                form.created_by.data = current_user.get_id()
            if hasattr(form, "last_updated_by"):
                form.last_updated_by.data = current_user.get_id()
                form.last_updated_at.data = datetime.datetime.now()

        if form.validate_on_submit():
            new_obj = self.create_function(form)
            db.session.add(new_obj)
            db.session.commit()
            if self.create_function.__name__ == "create_incident":
                remove_department_cache_entry(
                    Department(id=new_obj.department_id), KEY_DEPT_TOTAL_INCIDENTS
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
            # if the object doesn't have a creator id set it to current user
            if (
                hasattr(obj, "created_by")
                and hasattr(form, "created_by")
                and getattr(obj, "created_by")
            ):
                form.created_by.data = obj.created_by
            elif hasattr(form, "created_by"):
                form.created_by.data = current_user.get_id()

            # if the object keeps track of who updated it last, set to current user
            if hasattr(obj, "last_updated_by") and hasattr(form, "last_updated_by"):
                form.last_updated_by.data = current_user.get_id()
                form.last_updated_at.data = datetime.datetime.now()

        if hasattr(form, "department"):
            add_department_query(form, current_user)

        if form.validate_on_submit():
            self.populate_obj(form, obj)
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
        if hasattr(obj, "updated_at"):
            obj.updated_at = datetime.datetime.now()
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
