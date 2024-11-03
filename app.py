# app.py

from flask import Flask, send_from_directory, jsonify, request, session
from flask_cors import CORS  # Import CORS from flask_cors
from app.upload_images import upload_images_bp
from app.background_remover import ensure_directories
from pymongo import MongoClient
from bson.objectid import ObjectId
import bcrypt
from dotenv import load_dotenv
import os
import shutil
import threading
import time

# MongoDB connection string and Flask secret key
MONGO_URI = os.getenv('MONGO_URI')
SECRET_KEY = os.getenv('SECRET_KEY')

client = MongoClient(MONGO_URI)
db = client.get_database('bgremove')

app = Flask(__name__)
app.secret_key = SECRET_KEY
CORS(app)  # Apply CORS to your Flask app

# User collection in MongoDB
users_collection = db.users

# Register the blueprint for /upload route
app.register_blueprint(upload_images_bp)

# Function to ensure directories are created before handling any requests
def initialize():
    ensure_directories()

# Registering the initialize function to run before the first request
@app.before_request
def before_request():
    initialize()

# Function to clear contents of Uploads and Outputs folders
def clear_folders():
    uploads_dir = "assets/Uploads"
    outputs_dir = "assets/Outputs"

    while True:
        # Clear Uploads directory
        for filename in os.listdir(uploads_dir):
            file_path = os.path.join(uploads_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

        # Clear Outputs directory
        for session_dir in os.listdir(outputs_dir):
            session_path = os.path.join(outputs_dir, session_dir)
            try:
                shutil.rmtree(session_path)
            except Exception as e:
                print(f'Failed to delete {session_path}. Reason: {e}')

        # Sleep for 30 seconds before clearing again
        time.sleep(36000)

# Start the folder clearing function in a background thread
def start_clear_folder_thread():
    thread = threading.Thread(target=clear_folders)
    thread.daemon = True  # Daemonize thread to ensure it exits when the main program does
    thread.start()

# Start the folder clearing thread when the app starts
start_clear_folder_thread()

# Route to serve processed images
@app.route('/outputs/<session_id>/<filename>')
def uploaded_file(session_id, filename):
    directory = f"assets/Outputs/{session_id}"
    return send_from_directory(directory, filename)

#user routes
# get all users
@app.route('/users', methods=['GET'])
def get_all_users():
    users = list(users_collection.find())
    for user in users:
        user['_id'] = str(user['_id'])  # Convert ObjectId to string
        user.pop('password', None)  # Remove password field from response
    return jsonify(users), 200

# get user by id
@app.route('/users/<string:user_id>', methods=['GET'])
def get_user(user_id):
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    if user:
        user['_id'] = str(user['_id'])  # Convert ObjectId to string
        user.pop('password', None)  # Remove password field from response
        return jsonify(user), 200
    else:
        return 'User not found', 404
    
# login route
@app.route('/users/login', methods=['POST'])
def login():
    login_data = request.json
    email = login_data.get('email')
    password = login_data.get('password')

    # Check if email and password are provided
    if not email or not password:
        return 'Email and password are required', 400

    # Find user by email
    user = users_collection.find_one({'email': email})

    if user:
        # Verify hashed password
        if bcrypt.checkpw(password.encode('utf-8'), user['password']):
            # Store user's ObjectId in session
            session['user_id'] = str(user['_id'])
            return jsonify({'user_id': str(user['_id']), 'email': email}), 200
        else:
            return 'Invalid email or password', 401
    else:
        return 'Invalid email or password', 401

# logout route
@app.route('/users/logout', methods=['GET'])
def logout():
    # Clear the session
    session.clear()
    return 'Logged out successfully', 200

# create user route
@app.route('/users', methods=['POST'])
def create_user():
    new_user_data = request.json
    email = new_user_data.get('email')
    password = new_user_data.get('password')

    # Validate request data
    if not email or not password:
        return 'Email and password are required', 400
    
    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Create new user object with hashed password
    new_user = {
        'email': email,
        'password': hashed_password,  # Store hashed password in the database
    }

    # Insert new user into MongoDB
    result = users_collection.insert_one(new_user)
    return str(result.inserted_id), 201

# update user route
@app.route('/users/<string:user_id>', methods=['PUT'])
def update_user(user_id):
    update_data = request.json
    password = update_data.get('password')

    # Hash the password if provided in the update
    if password:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        update_data['password'] = hashed_password
    
    result = users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': update_data})
    if result.modified_count == 1:
        return 'Updated successfully', 200
    else:
        return 'User not found', 404

# delete user route
@app.route('/users/<string:user_id>', methods=['DELETE'])
def delete_user(user_id):
    result = users_collection.delete_one({'_id': ObjectId(user_id)})
    if result.deleted_count == 1:
        return 'Deleted successfully', 200
    else:
        return 'User not found', 404
    
# Change password route
@app.route('/users/<string:user_id>/change-password', methods=['POST'])
def change_password(user_id):
    change_password_data = request.json
    old_password = change_password_data.get('old_password')
    new_password = change_password_data.get('new_password')

    # Check if old and new password are provided
    if not old_password or not new_password:
        return 'Old and new password are required', 400

    # Find user by id
    user = users_collection.find_one({'_id': ObjectId(user_id)})

    if user:
        # Verify hashed password
        if bcrypt.checkpw(old_password.encode('utf-8'), user['password']):
            # Hash the new password
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            # Update user's password
            result = users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'password': hashed_password}})
            if result.modified_count == 1:
                return 'Password changed successfully', 200
            else:
                return 'Something went wrong', 500
        else:
            return 'Invalid old password', 401
    else:
        return 'User not found', 404

if __name__ == '__main__':
    # Only start the folder clearing thread if not in the reloader process
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        start_clear_folder_thread()
        
    app.run(debug=True, port=os.getenv("PORT", default=5000))
