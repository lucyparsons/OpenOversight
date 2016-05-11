import os
from flask import (render_template, request, redirect, url_for,
                  send_from_directory)
from werkzeug import secure_filename
from app import app
import pdb

from utils import allowed_file
from forms import FindOfficerForm


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/find')
def get_officer():
    form = FindOfficerForm()
    if form.validate_on_submit():
        flash('[DEBUG] Forms validate correctly')
        return redirect('/lineup')
    return render_template('input_find_officer.html', form=form)


@app.route('/lineup', methods=['GET', 'POST'])
def get_lineup():
    officers = ['Alice', 'Bob']
    form_values = request.form
    return render_template('lineup.html', officers=officers, form=form_values)


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
