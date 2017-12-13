from __future__ import print_function
import csv
import os
import re
from flask import Flask, request, redirect, url_for, render_template, flash
# from flask import send_from_directory
from werkzeug.utils import secure_filename
from qualtricskbfcsvimporter import QualtricsKBFCSVImporter


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['csv'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['SECRET_KEY'] = 'open!secret'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        legacy_file_format = request.form.get('checkbox_legacy_format', False)
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            results = ProcessCSVFile(os.path.join(app.config['UPLOAD_FOLDER'], filename), legacy_file_format)
            return render_template('results.html', matches=results['matches'])
    return render_template('index.html')


def ProcessCSVFile(csv_file, legacy_file_format):
    q = QualtricsKBFCSVImporter(csv_file, legacy_format=legacy_file_format)
    organization_matches = q.BestOrganizationFit()
    # Render in the template specified by path
    template_values = { 'respondents': q.respondents,
                        'organizations': q.organizations,
                        'organization_rankings': q.organization_rankings,
                        'matches': organization_matches }
    return template_values


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
