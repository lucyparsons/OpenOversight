from flask_wtf import FlaskForm as Form
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms import (StringField, DecimalField,
                     SelectField, IntegerField, SubmitField)
from wtforms.fields.html5 import DateField

from wtforms.validators import (DataRequired, AnyOf, NumberRange, Regexp,
                                Length, Optional)
from flask_wtf.file import FileField, FileAllowed, FileRequired

from ..utils import unit_choices


# Choices are a list of (value, label) tuples
RACE_CHOICES = [('BLACK', 'Black'), ('WHITE', 'White'), ('ASIAN', 'Asian'),
                ('HISPANIC', 'Hispanic'),
                ('PACIFIC ISLANDER', 'Pacific Islander'),
                ('Other', 'Other'), ('Not Sure', 'Not Sure')]
GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('Other', 'Other'),
                  ('Not Sure', 'Not Sure')]
RANK_CHOICES = [('Not Sure', 'Not Sure'), ('SUPT OF POLICE', 'Superintendent'),
                ('DEPUTY SUPT', 'Deputy Superintendent'), ('CHIEF', 'Chief'),
                ('DEP CHIEF', 'Deputy Chief'), ('COMMANDER', 'Commander'),
                ('CAPTAIN', 'Captain'), ('LIEUTENANT', 'Lieutenant'),
                ('SERGEANT', 'Sergeant'), ('FIELD', 'Field Training Officer'),
                ('PO', 'Police Officer')]
DEPT_CHOICES = [('ChicagoPD', 'Chicago Police Department')]


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
    dept = SelectField('dept', default='ChicagoPD', choices=DEPT_CHOICES,
                       validators=[DataRequired(),
                                   AnyOf(allowed_values(DEPT_CHOICES))])
    rank = SelectField('rank', default='Not Sure', choices=RANK_CHOICES,
                       validators=[AnyOf(allowed_values(RANK_CHOICES))])
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
    dept = SelectField('dept', default='ChicagoPD', choices=DEPT_CHOICES,
                       validators=[DataRequired(),
                                   AnyOf(allowed_values(DEPT_CHOICES))])


class FaceTag(Form):
    officer_id = IntegerField('officer_id', validators=[DataRequired()])
    image_id = IntegerField('image_id', validators=[DataRequired()])
    dataX = IntegerField('dataX', validators=[DataRequired()])
    dataY = IntegerField('dataY', validators=[DataRequired()])
    dataWidth = IntegerField('dataWidth', validators=[DataRequired()])
    dataHeight = IntegerField('dataHeight', validators=[DataRequired()])


class AssignmentForm(Form):
    star_no = IntegerField('star_no')
    rank = SelectField('rank', default='COMMANDER', choices=RANK_CHOICES,
                       validators=[AnyOf(allowed_values(RANK_CHOICES))])
    unit = QuerySelectField('unit', validators=[Optional()],
                            query_factory=unit_choices)
    star_date = DateField('star_date', validators=[Optional()])


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
