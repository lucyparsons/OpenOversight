import os
from flask import (render_template, request, redirect, url_for,
                  send_from_directory, flash)
from werkzeug import secure_filename
from app import app
import pdb
from sqlalchemy import create_engine

from utils import allowed_file, grab_officers
from forms import FindOfficerForm
import dbcred


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/find', methods=['GET', 'POST'])
def get_officer():
    form = FindOfficerForm()
    if form.validate_on_submit():
        pass
        #flash('[DEBUG] Forms validate correctly')
        return redirect(url_for('get_lineup'), code=307)
    return render_template('input_find_officer.html', form=form)


@app.route('/lineup', methods=['GET', 'POST'])
def get_lineup():
    engine = create_engine('postgresql://{}:{}@{}:{}/{}'.format(dbcred.user, dbcred.password,
                                                                dbcred.host, dbcred.port,
                                                                'chicagopolice'))
    form_values = request.form
    officers = grab_officers(form_values,  engine)
    #officer_images = []
    #for officer in officers:
    #    officer_images.append('http://placehold.it/400x300')
    return render_template('lineup.html', officers=officers, # officer_images=officer_images,
                           form=form_values)


@app.route('/submit')
def submit_data():
    return render_template('submit.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UNLABELLED_UPLOADS'], filename))
        return redirect(url_for('show_upload',
                                filename=filename))


@app.route('/show_upload/<filename>')
def show_upload(filename):
    #return send_from_directory('../'+config.UNLABELLED_UPLOADS,
    #                           filename)
    return 'Successfully uploaded: {}'.format(filename)


@app.route('/label')
def label_data():
    return render_template('label_data.html')


@app.route('/about')
def about_oo():
    return render_template('about.html')


@app.route('/contact')
def contact_oo():
    return render_template('contact.html')
