from flask import Flask, request, jsonify
from PIL import Image
import io

app = Flask(__name__)

@app.route('/process_image', methods=['POST'])
def process_image():
    # Get the image from the request
    file = request.files['file']
    image = Image.open(io.BytesIO(file.read()))

    # Process the image (e.g., detect error messages, etc.)
    # For example, let's just return the size of the image
    width, height = image.size
    return jsonify({"width": width, "height": height})

if __name__ == "__main__":
    app.run(debug=True)
