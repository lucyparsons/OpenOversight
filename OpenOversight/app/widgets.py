from markupsafe import Markup
from wtforms.fields import FormField
from wtforms.widgets.core import ListWidget, html_params


class BootstrapListWidget(ListWidget):
    def __init__(self, html_tag="ul", prefix_label=True, classes="list-unstyled"):
        super(BootstrapListWidget, self).__init__()
        self.classes = classes

    def __call__(self, field, **kwargs):
        c = kwargs.pop("classes", "") or kwargs.pop("class_", "")
        kwargs["class"] = f"{self.classes} {c}"
        kwargs.setdefault("id", field.id)
        html = [f"<{self.html_tag} {html_params(**kwargs)}>"]
        for subfield in field:
            if type(subfield) == FormField:
                html.append(f"<li><h6>{subfield.label.text}</h6> {subfield()}</li>")
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
        html.append(f"</{self.html_tag}>")
        return Markup("".join(html))


class FormFieldWidget(object):
    def __call__(self, field, **kwargs):
        html = []
        hidden = ""
        for subfield in field:
            if subfield.type == "HiddenField" or subfield.type == "CSRFTokenField":
                hidden += str(subfield)
            else:
                html.append(
                    '<div class="form-group">%s %s %s</div>'
                    % (str(subfield.label.text), hidden, str(subfield))
                )
                hidden = ""
        if hidden:
            html.append(hidden)
        return Markup("".join(html))
