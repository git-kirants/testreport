from flask import Flask, request, render_template, send_file
import firebase_admin
from firebase_admin import credentials, storage
import io
import PyPDF2
import re

app = Flask(__name__)

# Initialize Firebase Admin
cred = credentials.Certificate(
    'reportcardapp-fe480-firebase-adminsdk-wl5o9-55b90068ac.json'
)
firebase_admin.initialize_app(
    cred, {'storageBucket': 'reportcardapp-fe480.appspot.com'})


def list_pdf_files(class_name=None, month=None, year=None):
    bucket = storage.bucket()
    blobs = bucket.list_blobs()

    files = []

    for blob in blobs:
        file_name = blob.name

        # Assume files are named like 'class_month_year.pdf'
        if file_name.endswith('.pdf'):
            parts = file_name.split('_')

            if len(parts) == 3:
                file_class, file_month, file_year = parts[0], parts[1], parts[
                    2].replace('.pdf', '')

                if (class_name == file_class or class_name is None) and \
                   (month == file_month or month is None) and \
                   (year == file_year or year is None):
                    files.append(file_name)

    return files


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    class_name = request.form.get('class_name')
    month = request.form.get('month')
    year = request.form.get('year')

    # Get Emirates ID and ensure it's only digits
    emirates_id = re.sub(r'\D', '', request.form.get('emirates_id'))

    # Validate Emirates ID
    if len(emirates_id) != 15:
        return "Invalid Emirates ID. It should be exactly 15 digits."

    # List and filter PDF files based on class, month, and year
    files = list_pdf_files(class_name=class_name, month=month, year=year)

    if not files:
        return "No files found for the selected class, month, and year"

    # Assuming there's only one matching file for class, month, year
    file_name = files[0]

    bucket = storage.bucket()
    blob = bucket.blob(file_name)
    file_stream = io.BytesIO()
    blob.download_to_file(file_stream)
    file_stream.seek(0)

    emirates_id_page_map = {}

    pdf = PyPDF2.PdfReader(file_stream)
    outlines = pdf.outline
    for outline in outlines:
        if isinstance(outline, PyPDF2.generic.Destination):
            # Assuming the outline title is the Emirates ID
            clean_id = re.sub(r'\D', '', outline.title)
            page_no = pdf.get_destination_page_number(outline)
            emirates_id_page_map[clean_id] = page_no

    # Find the page associated with the given Emirates ID
    target_page_index = emirates_id_page_map.get(emirates_id)

    if target_page_index is not None:
        # Create a new PDF with just the target page
        output = PyPDF2.PdfWriter()
        output.add_page(pdf.pages[target_page_index])

        # Save the single page to a bytes buffer
        buffer = io.BytesIO()
        output.write(buffer)
        buffer.seek(0)

        # Return the PDF file as an attachment
        return send_file(buffer,
                         as_attachment=True,
                         download_name=f"emirates_id_{emirates_id}.pdf",
                         mimetype='application/pdf')
    else:
        return "Emirates ID not found in the selected report"


if __name__ == '__main__':
    app.run(debug=True)
