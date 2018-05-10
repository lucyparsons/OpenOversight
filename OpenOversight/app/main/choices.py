from us import states

# Choices are a list of (value, label) tuples
RACE_CHOICES = [('BLACK', 'Black'), ('WHITE', 'White'), ('ASIAN', 'Asian'),
                ('HISPANIC', 'Hispanic'),
                ('NATIVE AMERICAN', 'Native American'),
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

STATE_CHOICES = [('', '')] + [(state.abbr, state.name) for state in states.STATES]
LINK_CHOICES = [('', ''), ('link', 'Link'), ('video', 'YouTube Video')]
