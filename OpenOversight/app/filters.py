"""Contains all templates filters."""
from datetime import datetime
from zoneinfo import ZoneInfo

import bleach
import markdown as _markdown
from bleach_allowlist import markdown_attrs, markdown_tags
from flask import Flask, current_app, session
from markupsafe import Markup

from OpenOversight.app.utils.constants import (
    FIELD_NOT_AVAILABLE,
    KEY_TIMEZONE,
    OO_DATE_FORMAT,
    OO_TIME_FORMAT,
)
from OpenOversight.app.utils.general import AVAILABLE_TIMEZONES


def get_timezone() -> ZoneInfo:
    """Return the applicable timezone for the filter."""
    user_timezone = session.get(KEY_TIMEZONE)
    return ZoneInfo(
        user_timezone
        if user_timezone and user_timezone in AVAILABLE_TIMEZONES
        else current_app.config.get(KEY_TIMEZONE)
    )


def capfirst_filter(s: str) -> str:
    return s[0].capitalize() + s[1:]  # only change 1st letter


def get_age_from_birth_year(birth_year: int) -> int:
    return int(datetime.now(get_timezone()).year - birth_year)


def field_in_query(form_data, field) -> str:
    """
    Determine if a field is specified in the form data, and if so return a Bootstrap
    class which will render the field accordion open.
    """
    return " in " if form_data.get(field) else ""


def markdown(text: str) -> Markup:
    text = text.replace("\n", "  \n")  # make markdown not ignore new lines.
    html = bleach.clean(_markdown.markdown(text), markdown_tags, markdown_attrs)
    return Markup(html)


def display_date(value: datetime) -> str:
    """Convert UTC datetime.datetime into a localized date string."""
    if value:
        return value.strftime(OO_DATE_FORMAT)
    return FIELD_NOT_AVAILABLE


def local_date(value: datetime) -> str:
    """Convert UTC datetime.datetime into a localized date string."""
    if value:
        return value.astimezone(get_timezone()).strftime(OO_DATE_FORMAT)
    return FIELD_NOT_AVAILABLE


def local_date_time(value: datetime) -> str:
    """Convert UTC datetime.datetime into a localized date time string."""
    if value:
        return value.astimezone(get_timezone()).strftime(
            f"{OO_TIME_FORMAT} (%Z) on {OO_DATE_FORMAT}"
        )
    return FIELD_NOT_AVAILABLE


def display_time(value: datetime) -> str:
    """Convert UTC datetime.datetime into a localized date string."""
    # This is used for incident times which are not currently tz-aware
    if value:
        return value.strftime(OO_TIME_FORMAT)
    return FIELD_NOT_AVAILABLE


def local_time(value: datetime) -> str:
    """Convert UTC datetime.datetime into a localized time string."""
    if value:
        return value.astimezone(get_timezone()).strftime(f"{OO_TIME_FORMAT} (%Z)")
    return FIELD_NOT_AVAILABLE


def thousands_separator(value: int) -> str:
    """Convert int to string with the appropriately applied commas."""
    return f"{value:,}"


def display_currency(value: float) -> str:
    return f"${value:,.2f}"


def instantiate_filters(app: Flask):
    """Instantiate all template filters"""
    app.template_filter("capfirst")(capfirst_filter)
    app.template_filter("get_age")(get_age_from_birth_year)
    app.template_filter("field_in_query")(field_in_query)
    app.template_filter("markdown")(markdown)
    app.template_filter("display_date")(display_date)
    app.template_filter("local_date")(local_date)
    app.template_filter("local_date_time")(local_date_time)
    app.template_filter("display_time")(display_time)
    app.template_filter("local_time")(local_time)
    app.template_filter("thousands_separator")(thousands_separator)
    app.template_filter("display_currency")(display_currency)
