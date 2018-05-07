from flask_wtf import FlaskForm as Form
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms import (StringField, DecimalField,
                     SelectField, IntegerField, SubmitField)
from wtforms.fields.html5 import DateField

from wtforms.validators import (DataRequired, AnyOf, NumberRange, Regexp,
                                Length, Optional)
from flask_wtf.file import FileField, FileAllowed, FileRequired

from ..utils import unit_choices, dept_choices
from .choices import GENDER_CHOICES, RACE_CHOICES, RANK_CHOICES


def allowed_values(choices):
    return [x[0] for x in choices]


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
    rank = SelectField('rank', default='COMMANDER', choices=RANK_CHOICES,
                       validators=[AnyOf(allowed_values(RANK_CHOICES))])
    race = SelectField('race', default='WHITE', choices=RACE_CHOICES,
                       validators=[AnyOf(allowed_values(RACE_CHOICES))])
    gender = SelectField('gender', default='M', choices=GENDER_CHOICES,
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
    rank = SelectField('Rank', default='COMMANDER', choices=RANK_CHOICES,
                       validators=[AnyOf(allowed_values(RANK_CHOICES))])
    unit = QuerySelectField('Unit', validators=[Optional()],
                            query_factory=unit_choices, get_label='descrip')
    start_date = DateField('Assignment start date', validators=[Optional()])


class DepartmentForm(Form):
    name = StringField(
        'Full name of police department, e.g. Chicago Police Department',
        default='', validators=[Regexp('\w*'), Length(max=255), DataRequired()]
    )
    short_name = StringField(
        'Shortened acronym for police department, e.g. CPD',
        default='', validators=[Regexp('\w*'), Length(max=100), DataRequired()]
    )
    submit = SubmitField(label='Add')


class AddOfficerForm(Form):
    first_name = StringField('First name', default='', validators=[
        Regexp('\w*'), Length(max=50), Optional()])
    last_name = StringField('Last name', default='', validators=[
        Regexp('\w*'), Length(max=50), DataRequired()])
    middle_initial = StringField('Middle initial', default='', validators=[
        Regexp('\w*'), Length(max=50), Optional()])
    race = SelectField('Race', default='WHITE', choices=RACE_CHOICES,
                       validators=[AnyOf(allowed_values(RACE_CHOICES))])
    gender = SelectField('Gender', default='M', choices=GENDER_CHOICES,
                         validators=[AnyOf(allowed_values(GENDER_CHOICES))])
    star_no = StringField('Badge Number', default='', validators=[
        Regexp('\w*'), Length(max=50)])
    rank = SelectField('Rank', default='PO', choices=RANK_CHOICES,
                       validators=[AnyOf(allowed_values(RANK_CHOICES))])
    unit = QuerySelectField('Unit', validators=[Optional()],
                            query_factory=unit_choices, get_label='descrip',
                            allow_blank=True, blank_text=u'Unknown unit')
    employment_date = DateField('Employment Date', validators=[Optional()])
    birth_year = IntegerField('Birth Year', validators=[Optional()])
    department = QuerySelectField('Department', validators=[Optional()],
                                  query_factory=dept_choices, get_label='name')
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
    race = SelectField('Race', choices=RACE_CHOICES,
                       validators=[AnyOf(allowed_values(RACE_CHOICES))])
    gender = SelectField('Gender', choices=GENDER_CHOICES,
                         validators=[AnyOf(allowed_values(GENDER_CHOICES))])
    employment_date = DateField('Employment Date', validators=[Optional()])
    birth_year = IntegerField('Birth Year', validators=[Optional()])
    department = QuerySelectField(
        'Department',
        validators=[Optional()],
        query_factory=dept_choices,
        get_label='name')
    submit = SubmitField(label='Update')


class AddUnitForm(Form):
    descrip = StringField('Unit name or description', default='', validators=[
        Regexp('\w*'), Length(max=120), DataRequired()])
    department = QuerySelectField('Department', validators=[Optional()], get_label='name')
    submit = SubmitField(label='Add')
