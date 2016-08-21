from flask_wtf import Form
from wtforms import StringField, BooleanField, DecimalField, SelectField, IntegerField, FileField
from wtforms.validators import DataRequired, AnyOf, NumberRange
from flask_wtf.file import FileAllowed


# Choices are a list of (value, label) tuples
RACE_CHOICES = [('BLACK', 'Black'), ('WHITE', 'White'), ('ASIAN', 'Asian'),
                ('HISPANIC', 'Hispanic'), ('PACIFIC ISLANDER', 'Pacific Islander'), 
                ('Other', 'Other'), ('Not Sure', 'Not Sure')]
GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('Other', 'Other'),
                  ('Not Sure', 'Not Sure')]
RANK_CHOICES = [('Not Sure', 'Not Sure'), ('PO', 'Police Officer'),
                ('FIELD', 'Field Training Officer'), ('SERGEANT', 'Sergeant'),
                ('LIEUTENANT', 'Lieutenant'), 
                ('CAPTAIN', 'Captain'), ('COMMANDER', 'Commander'),
                ('DEP CHIEF', 'Deputy Chief'), ('CHIEF', 'Chief'), 
                ('DEPUTY SUPT', 'Deputy Superintendent'), ('SUPT OF POLICE', 'Superintendent')]
DEPT_CHOICES = [('ChicagoPD', 'Chicago Police Department')]


def allowed_values(choices):
    return [x[0] for x in choices]


class HumintContribution(Form):
    photo = FileField('image', validators=[
        DataRequired(),
        FileAllowed(['png', 'jpg', 'jpeg', 'mpg', 'mpeg', 'mp4', 'mov'], 
                    'Images and movies only!')
    ])


class FindOfficerForm(Form):
    dept = SelectField('dept', default='ChicagoPD', choices=DEPT_CHOICES,
                       validators=[DataRequired(),
                                   AnyOf(allowed_values(DEPT_CHOICES))])
    rank = SelectField('rank', default='Not Sure', choices=RANK_CHOICES,
                       validators=[AnyOf(allowed_values(RANK_CHOICES))])
    race = SelectField('race', default='Not Sure', choices=RACE_CHOICES,
                       validators=[AnyOf(allowed_values(RACE_CHOICES))])
    gender = SelectField('gender', default='Not Sure',
                         choices=GENDER_CHOICES, 
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

