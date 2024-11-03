import os
import uuid
from rembg import remove
from PIL import Image

UPLOAD_FOLDER = os.path.join('assets', 'Uploads')
OUTPUT_FOLDER = os.path.join('assets', 'Outputs')

def ensure_directories():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def handle_uploads(files):
    session_id = str(uuid.uuid4())
    session_upload_folder = os.path.join(UPLOAD_FOLDER, session_id)
    session_output_folder = os.path.join(OUTPUT_FOLDER, session_id)
    os.makedirs(session_upload_folder, exist_ok=True)
    os.makedirs(session_output_folder, exist_ok=True)

    uploaded_file_paths = []
    output_file_paths = []
    output_file_urls = []  # List to store generated URLs

    for file in files:
        if file and file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            unique_filename = f"{uuid.uuid4()}.png"
            input_path = os.path.join(session_upload_folder, unique_filename)
            file.save(input_path)
            uploaded_file_paths.append(input_path)

            try:
                # Open the image file
                original_local = Image.open(input_path)

                # Remove the background
                output = remove(original_local)

                # Save the processed image to the outputs directory as PNG
                output_path = os.path.join(session_output_folder, unique_filename)
                output.save(output_path, format="PNG")
                output_file_paths.append(output_path)

                # Generate URL for the processed image
                output_url = f"/outputs/{session_id}/{unique_filename}"  # Example URL format
                output_file_urls.append(output_url)

            except Exception as e:
                raise Exception(f"Error processing {file.filename}: {str(e)}")

    return session_id, uploaded_file_paths, output_file_paths, output_file_urls
