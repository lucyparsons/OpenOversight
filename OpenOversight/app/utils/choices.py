"""Contains choice lists of (value, label) tuples for form Select fields."""
from us import states


AGE_CHOICES = [(str(age), str(age)) for age in range(16, 101)]

GENDER_CHOICES = [
    ("Not Sure", "Not Sure"),
    ("M", "Male"),
    ("F", "Female"),
    ("Other", "Other"),
]

LINK_CHOICES = [
    ("", ""),
    ("link", "Link"),
    ("video", "YouTube Video"),
    ("other_video", "Other Video"),
]

RACE_CHOICES = [
    ("BLACK", "Black"),
    ("WHITE", "White"),
    ("ASIAN", "Asian"),
    ("HISPANIC", "Hispanic"),
    ("NATIVE AMERICAN", "Native American"),
    ("PACIFIC ISLANDER", "Pacific Islander"),
    ("Other", "Other"),
    ("Not Sure", "Not Sure"),
]

STATE_CHOICES = [(state.abbr, state.name) for state in states.STATES]
DEPARTMENT_STATE_CHOICES = [("FA", "Federal Agency")] + STATE_CHOICES

SUFFIX_CHOICES = [
    ("", "-"),
    ("Jr", "Jr"),
    ("Sr", "Sr"),
    ("II", "II"),
    ("III", "III"),
    ("IV", "IV"),
    ("V", "V"),
]
