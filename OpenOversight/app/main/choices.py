from us import states

# Choices are a list of (value, label) tuples
SUFFIX_CHOICES = [('', '-'), ('Jr', 'Jr'), ('Sr', 'Sr'), ('II', 'II'),
                  ('III', 'III'), ('IV', 'IV'), ('V', 'V')]
RACE_CHOICES = [('BLACK', 'Black'), ('WHITE', 'White'), ('ASIAN', 'Asian'),
                ('HISPANIC', 'Hispanic'),
                ('NATIVE AMERICAN', 'Native American'),
                ('PACIFIC ISLANDER', 'Pacific Islander'),
                ('Other', 'Other'), ('Not Sure', 'Not Sure')]

GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('Other', 'Other'),
                  ('Not Sure', 'Not Sure')]

RANK_CHOICES = [('SUPT OF POLICE', 'Superintendent'),
                ('DEPUTY SUPT', 'Deputy Superintendent'), ('CHIEF', 'Chief'),
                ('DEP CHIEF', 'Deputy Chief'), ('COMMANDER', 'Commander'),
                ('CAPTAIN', 'Captain'), ('LIEUTENANT', 'Lieutenant'),
                ('SERGEANT', 'Sergeant'), ('FIELD', 'Field Training Officer'),
                ('PO', 'Police Officer'), ('Not Sure', 'Not Sure')]

STATE_CHOICES = [('', '')] + [(state.abbr, state.name) for state in states.STATES]
LINK_CHOICES = [('', ''), ('link', 'Link'), ('video', 'YouTube Video'), ('other_video', 'Other Video')]
AGE_CHOICES = [(str(age), str(age)) for age in range(16, 101)]
