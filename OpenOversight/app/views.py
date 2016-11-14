import os
from flask import (render_template, request, redirect, url_for,
                   send_from_directory, flash, session)
from werkzeug import secure_filename
from app import app

from utils import allowed_file, grab_officers, roster_lookup
from forms import FindOfficerForm, FindOfficerIDForm
import config


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/find', methods=['GET', 'POST'])
def get_officer():
    form = FindOfficerForm()
    if form.validate_on_submit():
        #  flash('[DEBUG] Forms validate correctly')
        return redirect(url_for('get_gallery'), code=307)
    return render_template('input_find_officer.html', form=form)


@app.route('/tagger_gallery/<int:page>', methods=['POST'])
@app.route('/tagger_gallery', methods=['POST'])
def get_tagger_gallery(page=1):
    form = FindOfficerIDForm()
    if form.validate_on_submit():
        form_values = form.data
        officers = roster_lookup(form_values).paginate(page, config.OFFICERS_PER_PAGE, False)
        return render_template('tagger_gallery.html',
                               officers=officers,
                               form=form,
                               form_data=form_values)
    else:
        return redirect(url_for('label_data'))


@app.route('/gallery/<int:page>', methods=['POST'])
@app.route('/gallery', methods=['POST'])
def get_gallery(page=1):
    form = FindOfficerForm()
    if form.validate_on_submit():
        form_values = form.data
        officers = grab_officers(form_values).paginate(page, config.OFFICERS_PER_PAGE, False)
        return render_template('gallery.html',
                               officers=officers,
                               form=form,
                               form_data=form_values)
    else:
        return redirect(url_for('get_officer'))


@app.route('/complaint', methods=['GET', 'POST'])
def submit_complaint():
    return render_template('complaint.html',
                           officer_first_name=request.args.get('officer_first_name'),
                           officer_last_name=request.args.get('officer_last_name'),
                           officer_middle_initial=request.args.get('officer_middle_name'),
                           officer_star=request.args.get('officer_star'),
                           officer_image=request.args.get('officer_image'))


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
    # return send_from_directory('../'+config.UNLABELLED_UPLOADS,
    #                           filename)
    return 'Successfully uploaded: {}'.format(filename)


@app.route('/label', methods=['GET', 'POST'])
def label_data():
    form = FindOfficerForm()
    if form.validate_on_submit():
        #  flash('[DEBUG] Forms validate correctly')
        return redirect(url_for('get_tagger_gallery'), code=307)
    return render_template('label_data.html', form=form)


@app.route('/about')
def about_oo():
    return render_template('about.html')


@app.route('/contact')
def contact_oo():
    return render_template('contact.html')


@app.route('/privacy')
def privacy_oo():
    return render_template('privacy.html')
