import re
from datetime import datetime, time

from flask_wtf import FlaskForm as Form
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    FieldList,
    FormField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    URL,
    AnyOf,
    DataRequired,
    InputRequired,
    Length,
    NumberRange,
    Optional,
    Regexp,
    ValidationError,
)
from wtforms_sqlalchemy.fields import QuerySelectField

from OpenOversight.app.formfields import TimeField
from OpenOversight.app.models.database import Officer, db
from OpenOversight.app.utils.choices import (
    AGE_CHOICES,
    DEPARTMENT_STATE_CHOICES,
    GENDER_CHOICES,
    LINK_CHOICES,
    RACE_CHOICES,
    STATE_CHOICES,
    SUFFIX_CHOICES,
)
from OpenOversight.app.utils.db import dept_choices, unit_choices, unsorted_dept_choices
from OpenOversight.app.widgets import BootstrapListWidget, FormFieldWidget


# Normalizes the "not sure" option to what it needs to be when writing to the database.
# Note this should only be used for forms which save a record to the DB--not those that
# are used to look up existing records.
db_genders = list(GENDER_CHOICES)
for index, choice in enumerate(db_genders):
    if choice == ("Not Sure", "Not Sure"):
        db_genders[index] = (None, "Not Sure")  # type: ignore


def allowed_values(choices, empty_allowed=True):
    return [x[0] for x in choices if empty_allowed or x[0]]


def validate_money(form, field):
    if not re.fullmatch(r"\d+(\.\d\d)?0*", str(field.data)):
        raise ValidationError("Invalid monetary value")


def validate_end_date(form, field):
    if form.data["start_date"] and field.data:
        if form.data["start_date"] > field.data:
            raise ValidationError("End date must come after start date.")


class HumintContribution(Form):
    photo = FileField(
        "image",
        validators=[
            FileRequired(message="There was no file!"),
            FileAllowed(["png", "jpg", "jpeg"], message="Images only!"),
        ],
    )
    submit = SubmitField(label="Upload")


class FindOfficerForm(Form):
    # Any fields added to this form should generally also be added to BrowseForm
    first_name = StringField(
        "first_name",
        default="",
        validators=[Regexp(r"\w*"), Length(max=50), Optional()],
    )
    last_name = StringField(
        "last_name", default="", validators=[Regexp(r"\w*"), Length(max=50), Optional()]
    )
    badge = StringField(
        "badge", default="", validators=[Regexp(r"\w*"), Length(max=10)]
    )
    unique_internal_identifier = StringField(
        "unique_internal_identifier",
        default="",
        validators=[Regexp(r"\w*"), Length(max=55)],
    )
    # TODO: Figure out why this test is failing when the departments are sorted using
    #  the dept_choices function.
    dept = QuerySelectField(
        "dept",
        validators=[DataRequired()],
        query_factory=unsorted_dept_choices,
        get_label="display_name",
    )
    unit = StringField("unit", default="Not Sure", validators=[Optional()])
    current_job = BooleanField("current_job", default=None, validators=[Optional()])
    rank = StringField(
        "rank", default="Not Sure", validators=[Optional()]
    )  # Gets rewritten by Javascript
    race = SelectField(
        "race",
        default="Not Sure",
        choices=RACE_CHOICES,
        validators=[AnyOf(allowed_values(RACE_CHOICES))],
    )
    gender = SelectField(
        "gender",
        default="Not Sure",
        choices=GENDER_CHOICES,
        validators=[AnyOf(allowed_values(GENDER_CHOICES))],
    )
    min_age = IntegerField(
        "min_age", default=16, validators=[NumberRange(min=16, max=100)]
    )
    max_age = IntegerField(
        "max_age", default=85, validators=[NumberRange(min=16, max=100)]
    )
    require_photo = BooleanField(
        "require_photo", default=False, validators=[Optional()]
    )


class FaceTag(Form):
    officer_id = IntegerField("officer_id", validators=[DataRequired()])
    image_id = IntegerField("image_id", validators=[DataRequired()])
    dataX = IntegerField("dataX", validators=[InputRequired()])
    dataY = IntegerField("dataY", validators=[InputRequired()])
    dataWidth = IntegerField("dataWidth", validators=[InputRequired()])
    dataHeight = IntegerField("dataHeight", validators=[InputRequired()])


class AssignmentForm(Form):
    star_no = StringField(
        "Badge Number", default="", validators=[Regexp(r"\w*"), Length(max=50)]
    )
    job_title = QuerySelectField(
        "Job Title",
        validators=[DataRequired()],
        get_label="job_title",
        get_pk=lambda x: x.id,
    )  # query set in view function
    unit = QuerySelectField(
        "Unit",
        validators=[Optional()],
        query_factory=unit_choices,
        get_label="description",
        allow_blank=True,
        blank_text="None",
    )
    start_date = DateField("Assignment start date", validators=[Optional()])
    resign_date = DateField(
        "Assignment end date", validators=[Optional(), validate_end_date]
    )


class SalaryForm(Form):
    salary = DecimalField(
        "Salary",
        default=0,
        validators=[NumberRange(min=0, max=1000000), validate_money],
    )
    overtime_pay = DecimalField(
        "Overtime Pay",
        default=0,
        validators=[NumberRange(min=0, max=1000000), validate_money],
    )
    year = IntegerField(
        "Year",
        default=datetime.now().year,
        validators=[NumberRange(min=1900, max=2100)],
    )
    is_fiscal_year = BooleanField("Is fiscal year?", default=False)

    def validate(self, extra_validators=None):
        if not self.data.get("salary") and not self.data.get("overtime_pay"):
            return True
        return super(SalaryForm, self).validate(extra_validators=extra_validators)

    # def process(self, *args, **kwargs):
    # raise Exception(args[0])


class DepartmentForm(Form):
    name = StringField(
        "Full name of law enforcement agency, e.g. Chicago Police Department",
        default="",
        validators=[Regexp(r"\w*"), Length(max=255), DataRequired()],
    )
    short_name = StringField(
        "Shortened acronym for law enforcement agency, e.g. CPD",
        default="",
        validators=[Regexp(r"\w*"), Length(max=100), DataRequired()],
    )
    state = SelectField(
        "The law enforcement agency's home state",
        choices=[("", "Please Select a State")] + DEPARTMENT_STATE_CHOICES,
        default="",
        validators=[AnyOf(allowed_values(DEPARTMENT_STATE_CHOICES))],
    )
    jobs = FieldList(
        StringField("Job", default="", validators=[Regexp(r"\w*")]), label="Ranks"
    )
    submit = SubmitField(label="Add")


class EditDepartmentForm(DepartmentForm):
    submit = SubmitField(label="Update")


class LinkForm(Form):
    title = StringField(
        validators=[Length(max=100, message="Titles are limited to 100 characters.")],
        description="Text that will be displayed as the link.",
    )
    description = TextAreaField(
        validators=[
            Length(max=600, message="Descriptions are limited to 600 characters.")
        ],
        description="A short description of the link.",
    )
    author = StringField(
        validators=[Length(max=255, message="Limit of 255 characters.")],
        description="The source or author of the link.",
    )
    url = StringField(validators=[Optional(), URL(message="Not a valid URL")])
    link_type = SelectField(
        "Link Type",
        choices=LINK_CHOICES,
        default="",
        validators=[AnyOf(allowed_values(LINK_CHOICES))],
    )
    has_content_warning = BooleanField(
        "Include content warning?", default=True, validators=[Optional()]
    )

    def validate(self, extra_validators=None):
        success = super(LinkForm, self).validate(extra_validators=extra_validators)
        if self.url.data and not self.link_type.data:
            self.url.errors = list(self.url.errors)
            self.url.errors.append("Links must have a link type.")
            success = False

        return success


class OfficerLinkForm(LinkForm):
    officer_id = HiddenField(
        validators=[DataRequired(message="Not a valid officer ID")]
    )
    submit = SubmitField(label="Submit")


class BaseTextForm(Form):
    text_contents = TextAreaField()
    description = (
        "This information about the officer will be attributed to your username."
    )


class EditTextForm(BaseTextForm):
    submit = SubmitField(label="Submit")


class TextForm(EditTextForm):
    officer_id = HiddenField(
        validators=[DataRequired(message="Not a valid officer ID")]
    )


class AddOfficerForm(Form):
    department = QuerySelectField(
        "Department",
        validators=[DataRequired()],
        query_factory=dept_choices,
        get_label="display_name",
    )
    first_name = StringField(
        "First name",
        default="",
        validators=[Regexp(r"\w*"), Length(max=50), Optional()],
    )
    last_name = StringField(
        "Last name",
        default="",
        validators=[Regexp(r"\w*"), Length(max=50), DataRequired()],
    )
    middle_initial = StringField(
        "Middle initial",
        default="",
        validators=[Regexp(r"\w*"), Length(max=50), Optional()],
    )
    suffix = SelectField(
        "Suffix",
        default="",
        choices=SUFFIX_CHOICES,
        validators=[AnyOf(allowed_values(SUFFIX_CHOICES))],
    )
    race = SelectField(
        "Race",
        default="WHITE",
        choices=RACE_CHOICES,
        validators=[AnyOf(allowed_values(RACE_CHOICES))],
    )
    gender = SelectField(
        "Gender",
        choices=GENDER_CHOICES,
        coerce=lambda x: None if x == "Not Sure" else x,
        validators=[AnyOf(allowed_values(db_genders))],
    )
    star_no = StringField(
        "Badge Number", default="", validators=[Regexp(r"\w*"), Length(max=50)]
    )
    unique_internal_identifier = StringField(
        "Unique Internal Identifier",
        default="",
        validators=[Regexp(r"\w*"), Length(max=50)],
    )
    job_id = StringField("Job ID")  # Gets rewritten by Javascript
    unit = QuerySelectField(
        "Unit",
        validators=[Optional()],
        query_factory=unit_choices,
        get_label="description",
        allow_blank=True,
        blank_text="None",
    )
    employment_date = DateField("Employment Date", validators=[Optional()])
    birth_year = IntegerField("Birth Year", validators=[Optional()])
    links = FieldList(
        FormField(LinkForm, widget=FormFieldWidget()),
        description="Links to articles about or videos of the incident.",
        min_entries=1,
        widget=BootstrapListWidget(),
    )
    notes = FieldList(
        FormField(BaseTextForm, widget=FormFieldWidget()),
        description="This note about the officer will be attributed to your username.",
        min_entries=1,
        widget=BootstrapListWidget(),
    )
    descriptions = FieldList(
        FormField(BaseTextForm, widget=FormFieldWidget()),
        description="This description of the officer will be attributed to your username.",
        min_entries=1,
        widget=BootstrapListWidget(),
    )
    salaries = FieldList(
        FormField(SalaryForm, widget=FormFieldWidget()),
        description="Officer salaries",
        min_entries=1,
        widget=BootstrapListWidget(),
    )

    submit = SubmitField(label="Add")


class EditOfficerForm(Form):
    first_name = StringField(
        "First name", validators=[Regexp(r"\w*"), Length(max=50), Optional()]
    )
    last_name = StringField(
        "Last name", validators=[Regexp(r"\w*"), Length(max=50), DataRequired()]
    )
    middle_initial = StringField(
        "Middle initial", validators=[Regexp(r"\w*"), Length(max=50), Optional()]
    )
    suffix = SelectField(
        "Suffix",
        choices=SUFFIX_CHOICES,
        default="",
        validators=[AnyOf(allowed_values(SUFFIX_CHOICES))],
    )
    race = SelectField(
        "Race",
        choices=RACE_CHOICES,
        coerce=lambda x: x or None,
        validators=[AnyOf(allowed_values(RACE_CHOICES))],
    )
    gender = SelectField(
        "Gender",
        choices=GENDER_CHOICES,
        coerce=lambda x: None if x == "Not Sure" else x,
        validators=[AnyOf(allowed_values(db_genders))],
    )
    employment_date = DateField("Employment Date", validators=[Optional()])
    birth_year = IntegerField("Birth Year", validators=[Optional()])
    unique_internal_identifier = StringField(
        "Unique Internal Identifier",
        default="",
        validators=[Regexp(r"\w*"), Length(max=50)],
        filters=[lambda x: x or None],
    )
    department = QuerySelectField(
        "Department",
        validators=[Optional()],
        query_factory=dept_choices,
        get_label="display_name",
    )
    submit = SubmitField(label="Update")


class AddUnitForm(Form):
    description = StringField(
        "Unit name or description",
        default="",
        validators=[Regexp(r"\w*"), Length(max=120), DataRequired()],
    )
    department = QuerySelectField(
        "Department",
        validators=[DataRequired()],
        query_factory=dept_choices,
        get_label="display_name",
    )
    submit = SubmitField(label="Add")


class AddImageForm(Form):
    department = QuerySelectField(
        "Department",
        validators=[DataRequired()],
        query_factory=dept_choices,
        get_label="display_name",
    )


class DateFieldForm(Form):
    date_field = DateField("Date*", validators=[DataRequired()])
    time_field = TimeField("Time", validators=[Optional()])

    def validate_time_field(self, field):
        if not isinstance(field.data, time):
            raise ValidationError("Not a valid time.")

    def validate_date_field(self, field):
        if field.data.year < 1900:
            raise ValidationError("Incidents prior to 1900 not allowed.")


class LocationForm(Form):
    street_name = StringField(
        validators=[Optional()],
        description="Street on which incident occurred. For privacy reasons, please DO NOT INCLUDE street number.",
    )
    cross_street1 = StringField(
        validators=[Optional()],
        description="Closest cross street to where incident occurred.",
    )
    cross_street2 = StringField(validators=[Optional()])
    city = StringField("City*", validators=[DataRequired()])
    state = SelectField(
        "State*",
        choices=STATE_CHOICES,
        validators=[
            AnyOf(allowed_values(STATE_CHOICES, False), message="Must select a state.")
        ],
    )
    zip_code = StringField(
        "Zip Code",
        validators=[
            Optional(),
            Regexp(r"^\d{5}$", message="Zip codes must have 5 digits."),
        ],
    )


class LicensePlateForm(Form):
    number = StringField("Plate Number", validators=[])
    state = SelectField(
        "State",
        choices=STATE_CHOICES,
        validators=[AnyOf(allowed_values(STATE_CHOICES))],
    )

    def validate_state(self, field):
        if self.number.data != "" and field.data == "":
            raise ValidationError("Must also select a state.")


class OfficerIdField(StringField):
    def process_data(self, value):
        if isinstance(value, Officer):
            self.data = value.id
        else:
            self.data = value


def validate_oo_id(self, oo_id):
    if oo_id.data and isinstance(oo_id.data, str):
        if oo_id.data.isnumeric():
            officer = db.session.get(Officer, oo_id.data)
        else:
            try:
                officer_id = oo_id.data.split('value="')[1][:-2]
                officer = db.session.get(Officer, officer_id)

            # Sometimes we get a string in field.data with py.test, this parses it
            except IndexError:
                officer = None

        if not officer:
            raise ValidationError("Not a valid officer id")


class OOIdForm(Form):
    oo_id = StringField("OO Officer ID", validators=[validate_oo_id])


class IncidentForm(DateFieldForm):
    report_number = StringField(
        validators=[
            Regexp(
                r"^[a-zA-Z0-9- ]*$",
                message="Report cannot contain special characters (dashes permitted)",
            )
        ],
        description="Incident number for the organization tracking incidents",
    )
    description = TextAreaField(validators=[Optional()])
    department = QuerySelectField(
        "Department*",
        validators=[DataRequired()],
        query_factory=dept_choices,
        get_label="display_name",
    )
    address = FormField(LocationForm)
    officers = FieldList(
        FormField(OOIdForm, widget=FormFieldWidget()),
        description="Officers present at the incident.",
        min_entries=1,
        widget=BootstrapListWidget(),
    )
    license_plates = FieldList(
        FormField(LicensePlateForm, widget=FormFieldWidget()),
        description="License plates of police vehicles at the incident.",
        min_entries=1,
        widget=BootstrapListWidget(),
    )
    links = FieldList(
        FormField(LinkForm, widget=FormFieldWidget()),
        description="Links to articles about or videos of the incident.",
        min_entries=1,
        widget=BootstrapListWidget(),
    )

    submit = SubmitField(label="Submit")


class BrowseForm(Form):
    # Any fields added to this form should generally also be added to FindOfficerForm
    # query set in view function
    rank = QuerySelectField(
        "rank",
        validators=[Optional()],
        get_label="job_title",
        get_pk=lambda job: job.job_title,
    )
    # query set in view function
    unit = QuerySelectField(
        "unit",
        validators=[Optional()],
        get_label="description",
        get_pk=lambda unit: unit.description,
    )
    current_job = BooleanField("current_job", default=None, validators=[Optional()])
    name = StringField("Last name")
    badge = StringField("Badge number")
    unique_internal_identifier = StringField("Unique ID")
    race = SelectField(
        "race",
        default="Not Sure",
        choices=RACE_CHOICES,
        validators=[AnyOf(allowed_values(RACE_CHOICES))],
    )
    gender = SelectField(
        "gender",
        default="Not Sure",
        choices=GENDER_CHOICES,
        validators=[AnyOf(allowed_values(GENDER_CHOICES))],
    )
    min_age = SelectField(
        "minimum age",
        default=16,
        choices=AGE_CHOICES,
        validators=[AnyOf(allowed_values(AGE_CHOICES))],
    )
    max_age = SelectField(
        "maximum age",
        default=100,
        choices=AGE_CHOICES,
        validators=[AnyOf(allowed_values(AGE_CHOICES))],
    )
    require_photo = BooleanField(
        "require_photo", default=False, validators=[Optional()]
    )
    submit = SubmitField(label="Submit")


class IncidentListForm(Form):
    department_id = HiddenField("Department Id")
    report_number = StringField("Report Number")
    occurred_before = DateField("Occurred Before")
    occurred_after = DateField("Occurred After")
    submit = SubmitField(label="Submit")
