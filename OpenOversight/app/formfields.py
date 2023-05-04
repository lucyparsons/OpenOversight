import datetime

from wtforms import StringField
from wtforms.widgets import TimeInput


class TimeField(StringField):
    """HTML5 time input."""

    widget = TimeInput()

    def __init__(self, label=None, validators=None, format="%H:%M:%S", **kwargs):
        super(TimeField, self).__init__(label, validators, **kwargs)
        self.format = format

    def _value(self):
        if self.raw_data:
            return " ".join(self.raw_data)
        else:
            return self.data and self.data.strftime(self.format) or ""

    def process_formdata(self, valuelist):
        if valuelist and valuelist != [""]:
            time_str = " ".join(valuelist)
            try:
                components = time_str.split(":")
                hour = 0
                minutes = 0
                seconds = 0
                if len(components) in range(2, 4):
                    hour = int(components[0])
                    minutes = int(components[1])

                    if len(components) == 3:
                        seconds = int(components[2])
                else:
                    raise ValueError
                self.data = datetime.time(hour, minutes, seconds)
            except ValueError:
                self.data = None
                raise ValueError(self.gettext("Not a valid time"))
