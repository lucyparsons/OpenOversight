from wtforms.compat import text_type
from wtforms.fields import FormField
from wtforms.widgets.core import HTMLString, ListWidget, html_params


class BootstrapListWidget(ListWidget):
    def __init__(self, html_tag="ul", prefix_label=True, classes="list-unstyled"):
        super(BootstrapListWidget, self).__init__()
        self.classes = classes

    def __call__(self, field, **kwargs):
        c = kwargs.pop("classes", "") or kwargs.pop("class_", "")
        kwargs["class"] = "%s %s" % (self.classes, c)
        kwargs.setdefault("id", field.id)
        html = ["<%s %s>" % (self.html_tag, html_params(**kwargs))]
        for subfield in field:
            if type(subfield) == FormField:
                html.append(
                    "<li><h6>%s</h6> %s</li>" % (subfield.label.text, subfield())
                )
            if self.prefix_label:
                html.append(
                    '<li><div class="form-group">%s %s</div></li>'
                    % (subfield.label, subfield())
                )
            else:
                html.append(
                    '<li><div class="form-group">%s %s</div><</li>'
                    % (subfield(), subfield.label)
                )
        html.append("</%s>" % self.html_tag)
        return HTMLString("".join(html))


class FormFieldWidget(object):
    def __call__(self, field, **kwargs):
        html = []
        hidden = ""
        for subfield in field:
            if subfield.type == "HiddenField" or subfield.type == "CSRFTokenField":
                hidden += text_type(subfield)
            else:
                html.append(
                    '<div class="form-group">%s %s %s</div>'
                    % (text_type(subfield.label.text), hidden, text_type(subfield))
                )
                hidden = ""
        if hidden:
            html.append(hidden)
        return HTMLString("".join(html))
