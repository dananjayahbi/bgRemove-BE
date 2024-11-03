from flask import Blueprint, request, jsonify
from app.background_remover import handle_uploads
from flask_cors import CORS

# Allow all origins to access the /upload route
CORS(allow_headers='Content-Type', resources={r"/upload": {"origins": "*"}})

upload_images_bp = Blueprint('upload_images', __name__)

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
