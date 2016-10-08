from app import db


class Officer(db.Model):
    __tablename__ = 'officers'

    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(120), index=True, unique=False)
    first_name = db.Column(db.String(120), index=True, unique=False)
    middle_initial = db.Column(db.String(120), unique=False)
    race = db.Column(db.String(120), index=True, unique=False)
    gender = db.Column(db.String(120), index=True, unique=False)
    employment_date = db.Column(db.DateTime, index=True, unique=False)
    birth_year = db.Column(db.Integer, index=True, unique=False)

    def __repr__(self):
        return '<Officer ID {}: {} {} {}>'.format(self.id,
                                                  self.first_name,
                                                  self.middle_initial,
                                                  self.last_name)


class Assignment(db.Model):
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'))
    star_no = db.Column(db.Integer, index=True, unique=False)

    def __repr__(self):
        return '<Assignment: ID {} : {}>'.format(self.officer_id,
                                                 self.star_no)