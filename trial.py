from PyPDF2 import PdfReader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI  # Updated import
from langchain.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate  # Updated import
from langchain.chains import LLMChain  # Updated import
from flask import url_for
from flask import Flask, request, jsonify, render_template
import base64
import requests
import smtplib
from email.mime.text import MIMEText
import uuid
import openai
import json
import re
import os

with open('/Users/dhiveshakilan/Learning/Python/AI/IntelliAISupport/key.json') as f:
    key = json.load(f)

os.environ["OPENAI_API_KEY"] = key['API_KEY']

file_path = '/Users/dhiveshakilan/Learning/Python/AI/IntelliAISupport/Info Doc/'

# List of PDF files
pdf_files = ['AMGEO.pdf', 'Eliot.pdf', 'Error.pdf', 'Ole_feeding.pdf', 'role_access.pdf', 'gop_access.pdf', 'XDS.pdf', 'Sample_schema.pdf']

# Concatenate all the content from multiple PDFs
raw_text = ''

# Loop through each PDF file
for pdf_file in pdf_files:
    pdf = file_path + pdf_file
    pdfreader = PdfReader(pdf)

    # Read and extract text from each page in the PDF
    for i, page in enumerate(pdfreader.pages):
        content = page.extract_text()
        if content:
            raw_text += content

# Split the text using Character Text Split
text_splitter = CharacterTextSplitter(
    separator=".",
    chunk_size=200,
    chunk_overlap=20,
    length_function=len,
)
texts = text_splitter.split_text(raw_text)

# Download embeddings from OpenAI
embeddings = OpenAIEmbeddings()

document_search = FAISS.from_texts(texts, embeddings)

# Create chat prompt templates
system_message_template = SystemMessagePromptTemplate(content="You are a helpful assistant.")
human_message_template = HumanMessagePromptTemplate.from_template("{input}")
chat_prompt = ChatPromptTemplate.from_messages([system_message_template, human_message_template])

# Initialize ChatOpenAI model
llm = ChatOpenAI(temperature=0)

# Create the LLM chain
chain = LLMChain(llm=llm, prompt=chat_prompt)

app = Flask(__name__)

# Your existing user, gop_perimeter, gop_data, ptf_data, roles_data, counterpart_data, 
# and functions (account, gop_perimeter_check, encode_image, langchain_doc, etc.) go here...

# Replace langchain_doc function with LLMChain execution
def langchain_doc(query):
    docs = document_search.similarity_search(query)
    # Prepare the input for the LLMChain
    input_text = f"Given the following documents:\n{docs}\nAnswer the question: {query}"
    r = chain.run(input={"input": input_text})
    return r

# Your Flask routes and remaining logic...

user = {
        'login':
         {
            'akilan':{'active':'1','profile':'IT','mail':'dhivesh@gmail.com','sid':'da2024'},
            'suba': {'active':'1','profile':'TS','mail':'suba@gmail.com','sid':'sb2023'},
            'sanjay':{'active':'0','profile':'IT','mail':'sanjay@gmail.com','sid':'sk2022'},
            'shrishti':{'active':'1','profile':'RDA','mail':'shrishti@gmail.com','sid':'sh0404'}
         }
    }

gop_perimeter = {
            'IT':{'Gop':{'PDS'},'Perimeter':{'ABD','BCD'}},
            'TS':{'Gop':{},'Perimeter':{'ABD'}},
            'RD':{'Gop':{'*All*'},'Perimeter':{'BCD','KJH'}}
            }

gop_data = {
        "PDS": {"Perimeter": "ABD","Status": "Active","RDB" : "1234","Zone":"EUR"},
        "XYZ": {"Perimeter": "BCD","Status": "Active","RDB" : "2345","Zone":"USD"},
        "FX": {"Perimeter": "KJH","Status": "Not Active","RDB" : "3456","Zone":"HK"},
        "SNI": {"Perimeter": "BCD","Status": "Not Active","RDB" : "4567","Zone":"EUR"},
        "J3": {"Perimeter": "KJH","Status": "Active","RDB" : "5678","Zone":"EUR"}
    }
ptf_data = [
    {
        "PDS": [
            {"Portfolio": "PDS_ABC", "Status": "Active"},
            {"Portfolio": "PDS_XYZ", "Status": "Active"},
            {"Portfolio": "PDS_DEF", "Status": "Active"},
            {"Portfolio": "PDS_DEY", "Status": "Not Active"}
        ],
        "XYZ": [
            {"Portfolio": "XYZ_ABC", "Status": "Active"}
        ],
        "FX" : [
            {"Portfolio": "FX-GY-NOMGT", "Status": "Not Active"},
            {"Portfolio": "GY-MGT", "Status": "Not Active"}
        ],
        "SNI" : [
            {"Portfolio": "SN-FX-GY", "Status": "Not Active"}
        ],
        "J3" : [
            {"Portfolio": "JB-KJ-LI", "Status": "Active"}
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

counterpart_data = []

def account(id):
    if id in user['login']:
        if user['login'][id]['active'] == '1':
            profile = user['login'][id]['profile']
            print(f'Profile {profile}')
            return ['Account is active' , profile]
        else:
            return ['Account is not active.']
    else:
        return ['No user id found.']
    
def gop_perimeter_check(gop,profile):
    print(profile, gop_perimeter[profile]['Gop'],gop_perimeter[profile])
    if profile in gop_perimeter:  
        if gop in gop_perimeter[profile]['Gop']:
            return f'{gop} Gop access is already there.'
        else:
            gop_profile = gop_data[gop]['Perimeter']
            act_flg = gop_data[gop]['Status']
            if gop_profile in gop_perimeter[profile]['Perimeter']: 
                if act_flg == 'Active':
                    return f'Matching GOP: {gop}'
                else:
                    return f'Gop is not active.'
            else: 
                return f'User don\'t have access to {gop_profile} perimeter'
    else:
        return 'No profile found'

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


# Function to match user query with role keywords using partial matching
def match_role(role, roles_data):
    for i in range(len(roles_data)):
        if role.strip() in roles_data[i]['Role']:
            return f'{roles_data[i]['Role']} - {roles_data[i]['Description']}'
    return "No matching role found. - No description available"

def find_gop_using_ptf(ptf, ptf_data):
    found_gop=None
    for i,j in ptf_data[0].items():
        for k in range(len(j)):
            if j[k]['Portfolio'] in ptf.strip():
                found_gop = i if j[k]["Status"] == "Active" else "Portfolio not active"
                break
    return found_gop if found_gop is not None else "Not found"

def counterpart(user_query, counterpart_data):
    # No counterpart Found
    return

# You have not the authorization to perform this action. (technical authorizationn: RUN with discrimnant 'SNIKO' on process group 'EVENT PROCESSING')

def generate_request_id():
    return str(uuid.uuid4())

@app.route('/text', methods=['POST'])
def text():
    text_response = request.form.get('textMessage', '')
    k = langchain_doc(text_response)
    print(k)
    return jsonify({'response_message': k})

@app.route('/send_email', methods = ['POST'])
def send_approval_email():
    sender_email = "dhivesh18122000@gmail.com"  # Replace with your email
    sender_password = 'stwf byvp tuhv lskz'
    role = request.form['role']
    # print(role)
    user_id = request.form['userid']
    manager_email = request.form['managerEmail']
    # confirmation_message = request.form['confirmationMessage']
    request_id = generate_request_id()
    if 'role' in role.lower() or 'roles' in role.lower():
        rg = 'role'
    elif 'gop' in role.lower() or 'gops' in role.lower() or 'portfolio' in role.lower() or 'portfolios' in role.lower():
        rg = 'gop'

    subject = f"Approval Request for {rg} access"
    url=f'https://docs.google.com/forms/d/e/1FAIpQLScC4AvYbx9GIolMmjQQn62mfItYURw0mAZxUEyu4bWHN1ffNQ/viewform?usp=pp_url&entry.1314294973={request_id}&entry.1971473862={rg}'
    body = f'''Hello,
        User {user_id} is requesting access to the {rg}.
        The request ID for this approval is {request_id}.
        Please review and provide your approval on the below link.
        {url}

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
    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
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

    text_endpoint_url = request.host_url + 'text'  # Constructs the full URL for the /text endpoint
    text_response = requests.post(text_endpoint_url, data={'textMessage': user_query})

    if text_response.status_code != 200:
        return jsonify({"error": "Failed to process text", "details": text_response.json()}), text_response.status_code
    print(text_response.json())
    return text_response.json()

@app.route('/text_to_role', methods=['POST'])
def text_to_role():
    id = request.form.get('userid', '')
    text_message = request.form.get('textMessage', '')
    print(text_message)
    if not text_message:
        return jsonify({"error": "No text message provided"}), 400

    # query = "Why I am getting this message - "+text_message
    if 'role' in text_message.lower() or 'roles' in text_message.lower():
        q = f"Only return the role name from this response: {text_message}"
        matching = match_role(langchain_doc(q),roles_data)
        response_message = f"Matching Role: {matching}"
        print(response_message)

    elif 'portfolio' in text_message.lower() or 'portfolios' in text_message.lower() or 'gop' in text_message.lower() or 'gops' in text_message.lower():
        q1 = f"Only return the portfolio name from this response: {text_message}"
        matching = find_gop_using_ptf(langchain_doc(q1), ptf_data)
        print(matching)
        if matching != "Portfolio not active" and matching != "Not found":
            profile_id=account(id)
            if len(profile_id)>1:
                profile = f"{profile_id[1]}"
                print(profile)
                response_message = gop_perimeter_check(matching.strip(),profile)
            else:
                response_message= profile_id[0]
        else: 
            q = f"Only return the gop name from this response: {text_message}"
            matching = langchain_doc(q)
            print(matching)
            profile_id=account(id)
            if len(profile_id)>1:
                profile = f"{profile_id[1]}"
                print(profile)
                response_message = gop_perimeter_check(matching.strip(),profile)
            else:
                response_message= profile_id[0]

    elif 'counterpart' in text_message.lower():
        matching = counterpart(text_message, counterpart_data)
        response_message = f"Eliot Code is: {matching}"
    else:
        response_message = f"{text_message}"
    print(response_message)
    return jsonify({
        "extracted_message": text_message,
        "response_message": response_message
    })

if __name__ == '__main__':
    app.run(debug=True)
