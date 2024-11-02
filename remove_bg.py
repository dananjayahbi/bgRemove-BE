import os
import sys
import uuid
from rembg import remove
from PIL import Image

# Get the input and output directories from the command-line arguments
uploads_dir = sys.argv[1]
outputs_dir = sys.argv[2]

# Ensure the output directory exists
if not os.path.exists(outputs_dir):
    os.makedirs(outputs_dir)

# Loop through all files in the uploads directory
for filename in os.listdir(uploads_dir):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):  # Check for valid image files
        try:
            # Construct the full file path
            input_path = os.path.join(uploads_dir, filename)
            output_filename = f"{os.path.splitext(filename)[0]}.png"  # Change the extension to .png
            output_path = os.path.join(outputs_dir, output_filename)

            # Open the image file
            original_local = Image.open(input_path)

            # Remove the background
            output = remove(original_local)

            # Save the processed image to the outputs directory as PNG
            output.save(output_path, format="PNG")

            print(f"Processed and saved: {filename} as {output_filename}")

        except Exception as e:
            print(f"Error processing {filename}: {e}")

print("Processing complete.")
