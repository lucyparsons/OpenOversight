from us import states

# Choices are a list of (value, label) tuples
SUFFIX_CHOICES = [('', '-'), ('Jr', 'Jr'), ('Sr', 'Sr'), ('II', 'II'),
                  ('III', 'III'), ('IV', 'IV'), ('V', 'V')]
RACE_CHOICES = [('BLACK', 'Black or African American'), ('WHITE', 'White'),
                ('ASIAN PACIFIC ISLANDER', 'Asian/Pacific Islander'),
                ('HISPANIC', 'Hispanic'),
                ('NATIVE AMERICAN', 'American Indian/Alaska Native'),
                ('Other', 'Not Applicable (Non-U.S.)'),
                ('Not Sure', 'Not Specified')]

GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('Other', 'Other'),
                  ('Not Sure', 'Not Sure')]

RANK_CHOICES = [('Not Sure', 'Not Sure'), ('SUPT OF POLICE', 'Superintendent'),
                ('DEPUTY SUPT', 'Deputy Superintendent'), ('CHIEF', 'Chief'),
                ('DEP CHIEF', 'Deputy Chief'), ('COMMANDER', 'Commander'),
                ('CAPTAIN', 'Captain'), ('LIEUTENANT', 'Lieutenant'),
                ('SERGEANT', 'Sergeant'), ('FIELD', 'Field Training Officer'),
                ('PO', 'Police Officer')]

STATE_CHOICES = [('', '')] + [(state.abbr, state.name) for state in states.STATES]
LINK_CHOICES = [('', ''), ('link', 'Link'), ('video', 'YouTube Video'), ('other_video', 'Other Video')]
AGE_CHOICES = [(str(age), str(age)) for age in range(16, 101)]
