import os
from flask import (render_template, request, redirect, url_for,
                  send_from_directory, flash)
from werkzeug import secure_filename
from app import app
import pdb
from sqlalchemy import create_engine

from utils import allowed_file, grab_officers, grab_officer_faces
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

    officers = grab_officers(form_values, engine)
    results_dict = {}
    officer_ids, full_names = [], []
    for officer in officers:
        officer_id = officer[5]
        current_full_name = '{} {} {}'.format(officer[0], officer[1], officer[2])
        if current_full_name in full_names:
            continue
        else:
            full_names.append(current_full_name)
            results_dict.update({officer_id: { 
                'first_name': officer[0],
                'last_name': officer[2],
                'middle_initial': officer[1],
                'star_no': officer[8]
                }})
            officer_ids.append(officer_id)

    if len(officer_ids) > 0:
        officer_images = grab_officer_faces(officer_ids, engine)

    return render_template('lineup.html', officers=results_dict, form=form_values, 
                           officer_images=officer_images)


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

@app.route('/privacy')
def privacy_oo():
    return render_template('privacy.html')
