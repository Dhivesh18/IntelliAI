from flask import Flask, request, jsonify, render_template
import base64
import requests
import smtplib
from email.mime.text import MIMEText
import uuid
import openai
import json

# Load the JSON configuration
file_path = '/Users/dhiveshakilan/Learning/Python/AI/IntelliAISupport/key.json'
with open(file_path) as f:
    config = json.load(f)

api_key = config['API_KEY']

app = Flask(__name__)

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Function to match user query with role keywords using partial matching
def match_role(user_query, roles_data):
    for role in roles_data:
        keywords = role['Keywords'].split(', ')
        for keyword in keywords:
            if keyword in user_query:
                return role['Role'], role['Description']
    return "No matching role found.", "No description available"

def match_gop(user_query, gop_data):
    for gop in user_query.split():
        if gop in gop_data[0].keys():
            return gop
    return "No matching gop found."

def generate_request_id():
    return str(uuid.uuid4())

@app.route('/send_email', methods = ['POST'])
def send_approval_email():
    sender_email = "dhivesh18122000@gmail.com"  # Replace with your email
    sender_password = 'stwf byvp tuhv lskz'
    role = request.form['role']
    user_email = request.form['userEmail']
    manager_email = request.form['managerEmail']
    # confirmation_message = request.form['confirmationMessage']
    request_id = generate_request_id()
    subject = f"Approval Request for {role} - Reference ID: {request_id}"
    
    body = f'''Hello,
        User {user_email} is requesting access to the role or GOP: {role}.
        The request ID for this approval is {request_id}.
        Please review and provide your approval.
        Sincerely, 
        Eliot Team'''
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = manager_email

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return jsonify({'status': 'success', 'message': 'Approval email sent successfully.'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

gop_data = [
    {
        "DPS": [
            {"Portfolio": "PDS_ABC", "Status": "Active"},
            {"Portfolio": "PDS_XYZ", "Status": "Active"},
            {"Portfolio": "PDS_DEF", "Status": "Active"},
            {"Portfolio": "PDS_DEY", "Status": "Not Active"}
        ],
        "XYZ": [
            {"Portfolio": "XYZ_ABC", "Status": "Active"}
        ]
    }
]

roles_data = [
    {"Role": "DELETE_FLUX_X", "Description": "Delete flows via excel", "Keywords": "delete, flows, excel, not allowed to delete flows, no permission for deleting flows"},
    {"Role": "DELETE_OLD_DEAL_X", "Description": "Massive delete old deal x", "Keywords": "delete, old deals, massive delete, no permission for deleting deals, delete deal, not allowed to delete deals"},
    {"Role": "MAJ_FLOW_CVA", "Description": "Input of CVA Flows", "Keywords": "CVA, CVA flows, no access for CVA flows, unable to input CVA data"},
    {"Role": "MAJ_FLOW_OPERATIONEL", "Description": "Input of AJT, CLR, MTM Flows", "Keywords": "AJT flows, CLR flows, MTM flows, no permission for AJT, no access for CLR, unable to input MTM data, AJT, CLR, MTM"},
    {"Role": "MAJ_FLOW_TRESORESULT", "Description": "Input of FOR, RES, SAF, FIN, EMB, EMD Flows", "Keywords": "treasury result flows, FOR, RES, SAF, FIN, EMB, EMD, no permission for treasury flows, not allowed to input FOR data"},
    {"Role": "MAJ_FLOW_TSF_SHB", "Description": "Input of TSF/SHB Flows", "Keywords": "TSF, TSF flows, SHB flows, no access to TSF/SHB, unable to input TSF/SHB data"},
    {"Role": "RESULTAT_VALO", "Description": "Input of RHE, REM Flows", "Keywords": "RHE, RHE flows, REM flows, not allowed to input RHE/REM flows, no access for RHE/REM flows"},
    {"Role": "MAJ_FLOW_FLX", "Description": "Input of FLX Flows", "Keywords": "FLX, FLX flows, no permission for FLX flows, not allowed to input FLX data"},
    {"Role": "MAJ_FLOW_WHT", "Description": "Input of WHT Flows", "Keywords": "WHT, WHT flows, no access to WHT flows, unable to input WHT data"}
]


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/image_to_text', methods=['POST'])
def extract_and_match():
    if 'image' not in request.files:
        return jsonify({"error": "No image part found"}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({"error": "No image file selected"}), 400
    
    # Save the file temporarily
    file_path = '/tmp/' + file.filename
    file.save(file_path)
    
    base64_image = encode_image(file_path)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract only the error message text from this image."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    if response.status_code == 429:
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429

    if response.status_code != 200:
        return jsonify({"error": f"API request failed with status code {response.status_code}", "details": response.json()}), response.status_code

    try:
        response_json = response.json()
        user_query = response_json['choices'][0]['message']['content']
    except KeyError:
        return jsonify({"error": "Failed to parse response", "response": response.json()}), 500

    if not user_query:
        return jsonify({"error": "No message extracted"}), 400

    if 'Habilitation' in user_query:
        matching_role, description = match_role(user_query, roles_data)
        response_message = f"Matching Role: {matching_role}\nDescription: {description}"
    else:
        matching_role = match_gop(user_query, gop_data)
        response_message = f"Matching GOP: {matching_role}"

    return jsonify({
        "extracted_message": user_query,
        "response_message": response_message
    })

@app.route('/text_to_role', methods=['POST'])
def text_to_role():
    text_message = request.form.get('textMessage', '')
    
    if not text_message:
        return jsonify({"error": "No text message provided"}), 400
    
    if 'Habilitation' in text_message:
        matching_role, description = match_role(text_message, roles_data)
        response_message = f"Matching Role: {matching_role}\nDescription: {description}"
    else:
        matching_role = match_gop(text_message, gop_data)
        response_message = f"Matching GOP: {matching_role}"

    return jsonify({
        "extracted_message": text_message,
        "response_message": response_message
    })

if __name__ == '__main__':
    app.run(debug=True)

