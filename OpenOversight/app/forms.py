from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, DecimalField, SelectField, IntegerField, FileField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed


# Choices are a list of (value, label) tuples
RACE_CHOICES = [('Black', 'Black'), ('White', 'White'), ('Asian', 'Asian'),
                ('Hispanic', 'Hispanic'), ('Other', 'Other'), ('Not Sure', 'Not Sure')]
GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other'),
                  ('Not Sure', 'Not Sure')]
RANK_CHOICES = [('Not Sure', 'Not Sure'), ('SGT', 'Sergeant')]
DEPT_CHOICES = [('ChicagoPD', 'Chicago Police Department')]


class HumintContribution(Form):
    photo = FileField('image', validators=[
        DataRequired(),
        FileAllowed(['png', 'jpg', 'jpeg', 'mpg', 'mpeg', 'mp4', 'mov'], 
                    'Images and movies only!')
    ])


class FindOfficerForm(Form):
    dept = SelectField('dept', default='ChicagoPD', choices=DEPT_CHOICES,
                       validators=[DataRequired()])
    rank = SelectField('rank', default='Not Sure', choices=RANK_CHOICES)
    race = SelectField('race', default='Not Sure', choices=RACE_CHOICES)
    gender = SelectField('gender', default='Not Sure', choices=GENDER_CHOICES)
    min_age = IntegerField('min_age', default=16)
    max_age = IntegerField('max_age', default=85)
    latitude = DecimalField('latitude', default=False)
    longitude = DecimalField('longitude', default=False)
    upload = FileField('image', validators=[
        FileAllowed(['png', 'jpg', 'jpeg'], 'Images only!')
    ])
