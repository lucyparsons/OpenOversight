"""Contains all templates filters."""
import datetime

import bleach
import markdown as _markdown
import pytz as pytz
from bleach_allowlist import markdown_attrs, markdown_tags
from flask import Flask, session
from markupsafe import Markup

from OpenOversight.app.utils.constants import KEY_TIMEZONE


def instantiate_filters(app: Flask):
    """Instantiate all template filters"""

    @app.template_filter("capfirst")
    def capfirst_filter(s):
        return s[0].capitalize() + s[1:]  # only change 1st letter

    @app.template_filter("get_age")
    def get_age_from_birth_year(birth_year):
        if birth_year:
            return int(datetime.datetime.now().year - birth_year)

    @app.template_filter("field_in_query")
    def field_in_query(form_data, field):
        """
        Determine if a field is specified in the form data, and if so return a Bootstrap
        class which will render the field accordion open.
        """
        return " in " if form_data.get(field) else ""

    @app.template_filter("markdown")
    def markdown(text):
        text = text.replace("\n", "  \n")  # make markdown not ignore new lines.
        html = bleach.clean(_markdown.markdown(text), markdown_tags, markdown_attrs)
        return Markup(html)

    @app.template_filter("local_date")
    def local_date(value):
        """Convert UTC datetime.datetime into a localized date string."""
        return (
            pytz.timezone(session[KEY_TIMEZONE]).localize(value).strftime("%b %d, %Y")
        )

    @app.template_filter("local_date_time")
    def local_date_time(value):
        """Convert UTC datetime.datetime into a localized date time string."""
        app.logger.info("!!!!!!")
        app.logger.info(type(value))
        tz = pytz.timezone(session[KEY_TIMEZONE])
        if value.tzinfo is None:
            value = tz.localize(value)
        return dt.strftime("%I:%M %p on %b %d, %Y")

    @app.template_filter("local_time")
    def local_time(value):
        """Convert UTC datetime.datetime into a localized time string."""
        return pytz.timezone(session[KEY_TIMEZONE]).localize(value).strftime("%I:%M %p")
