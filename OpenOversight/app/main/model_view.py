from flask import render_template, redirect, request, url_for, flash, abort
from flask.views import MethodView
from ..auth.utils import admin_required
from ..models import db


class ModelView(MethodView):
    model = None
    model_name = ''
    per_page = 20
    order_by = ''
    form = ''

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

    def edit(self, id, form=None):
        obj = self.model.query.get_or_404(id)
        if not form:
            form = self.get_populated_form(obj)

        if form.validate_on_submit():
            self.populate_obj(form, obj)
            flash('{} successfully updated!'.format(self.model_name))
            return redirect(url_for('main.{}_api'.format(self.model_name), id=id, _method='GET'))

        return render_template('{}_edit.html'.format(self.model_name), obj=obj, form=form)

    def get_populated_form(self, obj):
        form = self.form(request.form, obj=obj)
        form.populate_obj(obj)
        return form


    def populate_obj(self, form, obj):
        form.populate_obj(obj)
        db.session.add(obj)


    def dispatch_request(self, *args, **kwargs):
        if request.method == 'GET':
            if request.url.split('/')[-1] == 'edit':
                meth = getattr(self, 'edit', None)
            else:
                meth = getattr(self, 'get', None)

        if request.method == 'POST':
            if request.url.split('/')[-1] == 'edit':
                meth = getattr(self, 'edit', None)
            else:
                abort(404)

        assert meth is not None, 'Unimplemented method %r' % request.method
        return meth(*args, **kwargs)
