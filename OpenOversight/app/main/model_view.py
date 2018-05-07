from flask import render_template, redirect, request, url_for, flash, current_app
from flask.views import MethodView


class ModelView(MethodView):
    model = None
    model_name = ''
    per_page = 20
    order_by = ''

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

