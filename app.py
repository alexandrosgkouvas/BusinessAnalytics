from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'uploads'
SAMPLED_FOLDER = 'sampled'
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SAMPLED_FOLDER'] = SAMPLED_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SAMPLED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    file_type = request.form['file_type']
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Read file based on type
        if file_type == 'csv':
            df = pd.read_csv(filepath)
        elif file_type == 'excel':
            df = pd.read_excel(filepath)
        elif file_type == 'txt':
            df = pd.read_csv(filepath, delimiter='\t')
        else:
            return "Unsupported file type", 400

        if len(df) > 50000:
            return render_template('sample_input.html', row_count=len(df), filename=filename, file_type=file_type)
        else:
            sampled_df = df.sample(n=min(len(df), 10000), random_state=1)
            sampled_path = os.path.join(app.config['UPLOAD_FOLDER'], 'sampled_' + filename)
            sampled_df.to_csv(sampled_path, index=False)

            preview = sampled_df.head(10).to_html(classes='table table-striped', index=False)
            shape = sampled_df.shape
            dtypes = sampled_df.dtypes.to_frame(name='Type').reset_index().rename(columns={'index': 'Column'})
            return render_template('preview.html',
                                   preview=preview,
                                   shape=shape,
                                   dtypes=dtypes.to_html(index=False, classes='table table-bordered'),
                                   download_file='sampled_' + filename)

@app.route('/sample', methods=['POST'])
def sample():
    filename = request.form['filename']
    file_type = request.form['file_type']
    sample_size = int(request.form['sample_size'])
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Read file again based on type
    if file_type == 'csv':
        df = pd.read_csv(filepath)
    elif file_type == 'excel':
        df = pd.read_excel(filepath)
    elif file_type == 'txt':
        df = pd.read_csv(filepath, delimiter='\t')
    else:
        return "Unsupported file type", 400

    sampled_df = df.sample(n=min(len(df), sample_size), random_state=1)
    sampled_path = os.path.join(app.config['UPLOAD_FOLDER'], 'sampled_' + filename)
    sampled_df.to_csv(sampled_path, index=False)

    preview = sampled_df.head(10).to_html(classes='table table-striped', index=False)
    shape = sampled_df.shape
    dtypes = sampled_df.dtypes.to_frame(name='Type').reset_index().rename(columns={'index': 'Column'})

    return render_template('preview.html',
                           preview=preview,
                           shape=shape,
                           dtypes=dtypes.to_html(index=False, classes='table table-bordered'),
                           download_file='sampled_' + filename)

@app.route('/uploads/<filename>')
def download_file(filename):
    # Ensure the file exists in the uploads folder
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        # Send the file for download
        response = send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

        # After the file is sent for download, we don't directly redirect; instead, set a cookie or similar.
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'

        # Return the response to trigger the download
        return response
    else:
        return "File not found", 404

@app.route('/start_download', methods=['POST'])
def start_download():
    filename = request.form['filename']
    return render_template('downloading.html', filename=filename)
@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

if __name__ == '__main__':
    app.run(debug=True)