from flask_wtf import FlaskForm as Form
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms import (StringField, DecimalField, TextAreaField,
                     SelectField, IntegerField, SubmitField,
                     HiddenField, FormField, FieldList, BooleanField)
from wtforms.fields.html5 import DateField

from wtforms.validators import (DataRequired, AnyOf, NumberRange, Regexp,
                                Length, Optional, Required, URL, ValidationError)
from flask_wtf.file import FileField, FileAllowed, FileRequired

from ..utils import unit_choices, dept_choices
from .choices import SUFFIX_CHOICES, GENDER_CHOICES, RACE_CHOICES, STATE_CHOICES, LINK_CHOICES, AGE_CHOICES
from ..formfields import TimeField
from ..widgets import BootstrapListWidget, FormFieldWidget
from ..models import Officer
import datetime
import re


def allowed_values(choices, empty_allowed=True):
    return [x[0] for x in choices if empty_allowed or x[0]]


def validate_money(form, field):
    if not re.fullmatch(r'\d+(\.\d\d)?0*', str(field.data)):
        raise ValidationError('Invalid monetary value')


class HumintContribution(Form):
    photo = FileField(
        'image', validators=[FileRequired(message='There was no file!'),
                             FileAllowed(['png', 'jpg', 'jpeg'],
                                         message='Images only!')]
    )
    submit = SubmitField(label='Upload')


class FindOfficerForm(Form):
    name = StringField(
        'name', default='', validators=[Regexp('\w*'), Length(max=50),
                                        Optional()]
    )
    badge = StringField('badge', default='', validators=[Regexp('\w*'),
                                                         Length(max=10)])
    dept = QuerySelectField('dept', validators=[DataRequired()],
                            query_factory=dept_choices, get_label='name')
    rank = StringField('rank', default='Not Sure', validators=[Optional()])
    race = SelectField('race', default='Not Sure', choices=RACE_CHOICES,
                       validators=[AnyOf(allowed_values(RACE_CHOICES))])
    gender = SelectField('gender', default='Not Sure', choices=GENDER_CHOICES,
                         validators=[AnyOf(allowed_values(GENDER_CHOICES))])
    min_age = IntegerField('min_age', default=16, validators=[
        NumberRange(min=16, max=100)
    ])
    max_age = IntegerField('max_age', default=85, validators=[
        NumberRange(min=16, max=100)
    ])
    latitude = DecimalField('latitude', default=False, validators=[
        NumberRange(min=-90, max=90)
    ])
    longitude = DecimalField('longitude', default=False, validators=[
        NumberRange(min=-180, max=180)
    ])


class FindOfficerIDForm(Form):
    name = StringField(
        'name', default='', validators=[
            Regexp('\w*'), Length(max=50), Optional()
        ]
    )
    badge = StringField(
        'badge', default='', validators=[Regexp('\w*'), Length(max=10)]
    )
    dept = QuerySelectField('dept', validators=[Optional()],
                            query_factory=dept_choices, get_label='name')


class FaceTag(Form):
    officer_id = IntegerField('officer_id', validators=[DataRequired()])
    image_id = IntegerField('image_id', validators=[DataRequired()])
    dataX = IntegerField('dataX', validators=[DataRequired()])
    dataY = IntegerField('dataY', validators=[DataRequired()])
    dataWidth = IntegerField('dataWidth', validators=[DataRequired()])
    dataHeight = IntegerField('dataHeight', validators=[DataRequired()])


class AssignmentForm(Form):
    star_no = StringField('Badge Number', default='', validators=[
        Regexp('\w*'), Length(max=50)])
    rank = StringField('Rank', default='', validators=[
        DataRequired(), Regexp('\w*')])
    unit = QuerySelectField('Unit', validators=[Optional()],
                            query_factory=unit_choices, get_label='descrip')
    star_date = DateField('Assignment start date', validators=[Optional()])


class SalaryForm(Form):
    salary = DecimalField('Salary', validators=[
        NumberRange(min=0, max=1000000), validate_money
    ])
    overtime_pay = DecimalField('Overtime Pay', validators=[
        NumberRange(min=0, max=1000000), validate_money
    ])
    year = IntegerField('Year', default=datetime.datetime.now().year, validators=[
        NumberRange(min=1900, max=2100)
    ])
    is_fiscal_year = BooleanField('Is fiscal year?', default=False)

    def validate(form, extra_validators=()):
        if not form.data.get('salary') and not form.data.get('overtime_pay'):
            return True
        return super(SalaryForm, form).validate()

    # def process(self, *args, **kwargs):
        # raise Exception(args[0])


class DepartmentForm(Form):
    name = StringField(
        'Full name of law enforcement agency, e.g. Chicago Police Department',
        default='', validators=[Regexp('\w*'), Length(max=255), DataRequired()]
    )
    short_name = StringField(
        'Shortened acronym for law enforcement agency, e.g. CPD',
        default='', validators=[Regexp('\w*'), Length(max=100), DataRequired()]
    )
    submit = SubmitField(label='Add')


class EditDepartmentForm(DepartmentForm):
    submit = SubmitField(label='Update')


class LinkForm(Form):
    title = StringField(
        validators=[Length(max=100, message='Titles are limited to 100 characters.')],
        description='Text that will be displayed as the link.')
    description = TextAreaField(
        validators=[Length(max=600, message='Descriptions are limited to 600 characters.')],
        description='A short description of the link.')
    author = StringField(
        validators=[Length(max=255, message='Limit of 255 characters.')],
        description='The source or author of the link.')
    url = StringField(validators=[Optional(), URL(message='Not a valid URL')])
    link_type = SelectField(
        'Link Type',
        choices=LINK_CHOICES,
        default='',
        validators=[AnyOf(allowed_values(LINK_CHOICES))])
    user_id = HiddenField(validators=[Required(message='Not a valid user ID')])

    def validate(self):
        success = super(LinkForm, self).validate()
        if self.url.data and not self.link_type.data:
            self.url.errors = list(self.url.errors)
            self.url.errors.append('Links must have a link type.')
            success = False

        return success


class BaseTextForm(Form):
    text_contents = TextAreaField()
    description = "This information about the officer will be attributed to your username."


class EditTextForm(BaseTextForm):
    submit = SubmitField(label='Submit')


class TextForm(EditTextForm):
    officer_id = HiddenField(validators=[Required(message='Not a valid officer ID')])
    creator_id = HiddenField(validators=[Required(message='Not a valid user ID')])


class AddOfficerForm(Form):
    first_name = StringField('First name', default='', validators=[
        Regexp('\w*'), Length(max=50), Optional()])
    last_name = StringField('Last name', default='', validators=[
        Regexp('\w*'), Length(max=50), DataRequired()])
    middle_initial = StringField('Middle initial', default='', validators=[
        Regexp('\w*'), Length(max=50), Optional()])
    suffix = SelectField('Suffix', default='', choices=SUFFIX_CHOICES,
                         validators=[AnyOf(allowed_values(SUFFIX_CHOICES))])
    race = SelectField('Race', default='WHITE', choices=RACE_CHOICES,
                       validators=[AnyOf(allowed_values(RACE_CHOICES))])
    gender = SelectField('Gender', default='M', choices=GENDER_CHOICES,
                         validators=[AnyOf(allowed_values(GENDER_CHOICES))])
    star_no = StringField('Badge Number', default='', validators=[
        Regexp('\w*'), Length(max=50)])
    unique_internal_identifier = StringField('Unique Internal Identifier', default='', validators=[Regexp('\w*'), Length(max=50)])
    rank = StringField('rank', default='', validators=[
        Optional(), Regexp('\w*')])
    unit = QuerySelectField('Unit', validators=[Optional()],
                            query_factory=unit_choices, get_label='descrip',
                            allow_blank=True, blank_text=u'Unknown unit')
    employment_date = DateField('Employment Date', validators=[Optional()])
    birth_year = IntegerField('Birth Year', validators=[Optional()])
    department = QuerySelectField('Department', validators=[Optional()],
                                  query_factory=dept_choices, get_label='name')
    links = FieldList(FormField(
        LinkForm,
        widget=FormFieldWidget()),
        description='Links to articles about or videos of the incident.',
        min_entries=1,
        widget=BootstrapListWidget())
    notes = FieldList(FormField(
        BaseTextForm,
        widget=FormFieldWidget()),
        description='This note about the officer will be attributed to your username.',
        min_entries=1,
        widget=BootstrapListWidget())
    descriptions = FieldList(FormField(
        BaseTextForm,
        widget=FormFieldWidget()),
        description='This description of the officer will be attributed to your username.',
        min_entries=1,
        widget=BootstrapListWidget())
    salaries = FieldList(FormField(
        SalaryForm,
        widget=FormFieldWidget()),
        description='Officer salaries',
        min_entries=1,
        widget=BootstrapListWidget())

    submit = SubmitField(label='Add')


class EditOfficerForm(Form):
    first_name = StringField('First name',
                             validators=[Regexp('\w*'), Length(max=50),
                                         Optional()])
    last_name = StringField('Last name',
                            validators=[Regexp('\w*'), Length(max=50),
                                        DataRequired()])
    middle_initial = StringField('Middle initial',
                                 validators=[Regexp('\w*'), Length(max=50),
                                             Optional()])
    suffix = SelectField('Suffix', choices=SUFFIX_CHOICES, default='',
                         validators=[AnyOf(allowed_values(SUFFIX_CHOICES))])
    race = SelectField('Race', choices=RACE_CHOICES, coerce=lambda x: x or None,
                       validators=[AnyOf(allowed_values(RACE_CHOICES))])
    gender = SelectField('Gender', choices=GENDER_CHOICES, coerce=lambda x: x or None,
                         validators=[AnyOf(allowed_values(GENDER_CHOICES))])
    employment_date = DateField('Employment Date', validators=[Optional()])
    birth_year = IntegerField('Birth Year', validators=[Optional()])
    unique_internal_identifier = StringField('Unique Internal Identifier',
                                             default='',
                                             validators=[Regexp('\w*'), Length(max=50)],
                                             filters=[lambda x: x or None])
    department = QuerySelectField(
        'Department',
        validators=[Optional()],
        query_factory=dept_choices,
        get_label='name')
    links = FieldList(FormField(
        LinkForm,
        widget=FormFieldWidget()),
        description='Links to articles about or videos of the officer.',
        min_entries=1,
        widget=BootstrapListWidget())
    submit = SubmitField(label='Update')


class AddUnitForm(Form):
    descrip = StringField('Unit name or description', default='', validators=[
        Regexp('\w*'), Length(max=120), DataRequired()])
    department = QuerySelectField(
        'Department',
        validators=[Required()],
        query_factory=dept_choices,
        get_label='name')
    submit = SubmitField(label='Add')


class AddImageForm(Form):
    department = QuerySelectField(
        'Department',
        validators=[Required()],
        query_factory=dept_choices,
        get_label='name')


class DateFieldForm(Form):
    date_field = DateField('Date <span class="text-danger">*</span>', validators=[Required()])
    time_field = TimeField('Time', validators=[Optional()])

    @property
    def datetime(self):
        if self.time_field.data:
            return datetime.datetime.combine(self.date_field.data,
                                             self.time_field.data)
        else:  # Code these events at a precise time so we can find them later
            coded_no_time = datetime.time(1, 2, 3, 45678)
            return datetime.datetime.combine(self.date_field.data,
                                             coded_no_time)

    @datetime.setter
    def datetime(self, value):
        self.date_field.data = value.date()
        self.time_field.data = value.time()

    def validate_time_field(self, field):
        if not type(field.data) == datetime.time:
            raise ValidationError('Not a valid time.')

    def validate_date_field(self, field):
        if field.data.year < 1900:
            raise ValidationError('Incidents prior to 1900 not allowed.')


class LocationForm(Form):
    street_name = StringField(validators=[Optional()], description='Street on which incident occurred. For privacy reasons, please DO NOT INCLUDE street number.')
    cross_street1 = StringField(validators=[Optional()], description='Closest cross street to where incident occurred.')
    cross_street2 = StringField(validators=[Optional()])
    city = StringField('City <span class="text-danger">*</span>', validators=[Required()])
    state = SelectField('State <span class="text-danger">*</span>', choices=STATE_CHOICES,
                        validators=[AnyOf(allowed_values(STATE_CHOICES, False), message='Must select a state.')])
    zip_code = StringField('Zip Code',
                           validators=[Optional(),
                                       Regexp('^\d{5}$', message='Zip codes must have 5 digits.')])


class LicensePlateForm(Form):
    number = StringField('Plate Number', validators=[])
    state = SelectField('State', choices=STATE_CHOICES,
                        validators=[AnyOf(allowed_values(STATE_CHOICES))])

    def validate_state(self, field):
        if self.number.data != '' and field.data == '':
            raise ValidationError('Must also select a state.')


class OfficerIdField(StringField):
    def process_data(self, value):
        if type(value) == Officer:
            self.data = value.id
        else:
            self.data = value


def validate_oo_id(self, field):
    if field.data:
        try:
            officer_id = int(field.data)
            officer = Officer.query.get(officer_id)

        # Sometimes we get a string in field.data with py.test, this parses it
        except ValueError:
            officer_id = field.data.split("value=\"")[1][:-2]
            officer = Officer.query.get(officer_id)

        if not officer:
            raise ValidationError('Not a valid officer id')


class OOIdForm(Form):
    oo_id = StringField('OO Officer ID', validators=[validate_oo_id])


class IncidentForm(DateFieldForm):
    report_number = StringField(
        validators=[Regexp(r'^[a-zA-Z0-9-]*$', message="Report numbers can contain letters, numbers, and dashes")],
        description='Incident number for the organization tracking incidents')
    description = TextAreaField(validators=[Optional()])
    department = QuerySelectField(
        'Department <span class="text-danger">*</span>',
        validators=[Required()],
        query_factory=dept_choices,
        get_label='name')
    address = FormField(LocationForm)
    officers = FieldList(FormField(
        OOIdForm, widget=FormFieldWidget()),
        description='Officers present at the incident.',
        min_entries=1,
        widget=BootstrapListWidget())
    license_plates = FieldList(FormField(
        LicensePlateForm, widget=FormFieldWidget()),
        description='License plates of police vehicles at the incident.',
        min_entries=1,
        widget=BootstrapListWidget())
    links = FieldList(FormField(
        LinkForm,
        widget=FormFieldWidget()),
        description='Links to articles about or videos of the incident.',
        min_entries=1,
        widget=BootstrapListWidget())
    creator_id = HiddenField(validators=[Required(message='Incidents must have a creator id.')])
    last_updated_id = HiddenField(validators=[Required(message='Incidents must have a user id for editing.')])

    submit = SubmitField(label='Submit')


class BrowseForm(Form):
    rank = QuerySelectField('rank', validators=[Optional()], get_label='rank',
                            get_pk=lambda rank: rank.rank)  # query set in view function
    race = SelectField('race', default='Not Sure', choices=RACE_CHOICES,
                       validators=[AnyOf(allowed_values(RACE_CHOICES))])
    gender = SelectField('gender', default='Not Sure', choices=GENDER_CHOICES,
                         validators=[AnyOf(allowed_values(GENDER_CHOICES))])
    min_age = SelectField('minimum age', default=16, choices=AGE_CHOICES,
                          validators=[AnyOf(allowed_values(AGE_CHOICES))])
    max_age = SelectField('maximum age', default=100, choices=AGE_CHOICES,
                          validators=[AnyOf(allowed_values(AGE_CHOICES))])
    submit = SubmitField(label='Submit')
