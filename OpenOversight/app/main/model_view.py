from flask import render_template, redirect, request, url_for, flash, abort
from flask.views import MethodView
from flask_login import login_required
from ..auth.utils import ac_or_admin_required
from ..models import db


class ModelView(MethodView):
    model = None
    model_name = ''
    per_page = 20
    order_by = ''
    form = ''
    create_function = ''

    def get(self, id):
        if id is None:
            if request.args.get('page'):
                page = int(request.args.get('page'))
            else:
                page = 1

            if self.order_by:
                objects = self.model.query.order_by(getattr(self.model, self.order_by)).paginate(page, self.per_page, False)
            else:
                objects = self.model.query.paginate(page, self.per_page, False)

            return render_template('{}_list.html'.format(self.model_name), objects=objects, url='main.{}_api'.format(self.model_name))
        else:
            obj = self.model.query.get_or_404(id)
            return render_template('{}_detail.html'.format(self.model_name), obj=obj)

    @login_required
    @ac_or_admin_required
    def new(self, form=None):
        form = self.form()
        if form.validate_on_submit():
            new_instance = self.create_function(form)
            db.session.add(new_instance)
            db.session.commit()

            return redirect(url_for('main.{}_api'.format(self.model_name), id=new_instance.id, _method='GET'))

        return render_template('{}_new.html'.format(self.model_name), form=form)

    @login_required
    @ac_or_admin_required
    def edit(self, id, form=None):
        obj = self.model.query.get_or_404(id)
        if not form:
            form = self.get_form(obj)

        if form.validate_on_submit():
            self.populate_obj(form, obj)
            flash('{} successfully updated!'.format(self.model_name))
            return redirect(url_for('main.{}_api'.format(self.model_name), id=id, _method='GET'))

        return render_template('{}_edit.html'.format(self.model_name), obj=obj, form=form)

    @login_required
    @ac_or_admin_required
    def delete(self, id):
        obj = self.model.query.get_or_404(id)
        if request.method == 'POST':
            db.session.delete(obj)
            db.session.commit()

            return redirect(url_for('main.{}_api'.format(self.model_name)))

        return render_template('{}_delete.html'.format(self.model_name), obj=obj)

    def get_form(self, obj):
        return self.form(request.form, obj=obj)

    def populate_obj(self, form, obj):
        form.populate_obj(obj)
        db.session.add(obj)

    def create_obj(self, form):
        self.model(**form.data)

    def dispatch_request(self, *args, **kwargs):
        end_of_url = request.url.split('/')[-1]
        if request.method == 'GET':
            if end_of_url == 'edit':
                meth = getattr(self, 'edit', None)
            elif end_of_url == 'delete':
                meth = getattr(self, 'delete', None)
            elif end_of_url == 'new':
                meth = getattr(self, 'new', None)
            else:
                meth = getattr(self, 'get', None)

        if request.method == 'POST':
            if end_of_url == 'edit':
                meth = getattr(self, 'edit', None)
            elif end_of_url == 'delete':
                meth = getattr(self, 'delete', None)
            elif end_of_url == 'new':
                meth = getattr(self, 'new', None)
            else:
                abort(404)

        assert meth is not None, 'Unimplemented method %r' % request.method
        return meth(*args, **kwargs)
