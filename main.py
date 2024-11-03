from flask import Flask, Blueprint, send_from_directory, jsonify, request, session
from background_remover import handle_uploads, ensure_directories
from flask_cors import CORS
import os
from bson.objectid import ObjectId
import shutil
import threading
import time

app = Flask(__name__)
CORS(app)

# Create a blueprint for /upload route
upload_images_bp = Blueprint('upload_images', __name__)

# Define the route for /upload
@upload_images_bp.route('/upload', methods=['POST'])
def upload_images():
    if 'files' not in request.files:
        return jsonify({'error': 'No files part in the request'}), 400

    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No files uploaded'}), 400

    try:
        session_id, uploaded_file_paths, output_file_paths, output_file_urls = handle_uploads(files)
        return jsonify({
            'session_id': session_id,
            'uploaded_files': uploaded_file_paths,
            'processed_files': output_file_paths,
            'processed_file_urls': output_file_urls  # Include URLs in the response
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Register the blueprint for /upload route
app.register_blueprint(upload_images_bp)

# Function to ensure directories are created before handling any requests
def initialize():
    ensure_directories()

# Registering the initialize function to run before the first request
@app.before_request
def before_request():
    initialize()

# Route to serve processed images
@app.route('/outputs/<session_id>/<filename>')
def uploaded_file(session_id, filename):
    directory = f"assets/Outputs/{session_id}"
    return send_from_directory(directory, filename)

@app.route('/')
def hello():
    return jsonify({'message': 'Hello World!'})

if __name__ == '__main__':
    app.run(debug=True)
