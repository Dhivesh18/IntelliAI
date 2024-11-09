from PyPDF2 import PdfReader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from flask import url_for
from flask import Flask, request, jsonify, render_template
import base64
import requests
import smtplib
from email.mime.text import MIMEText
# from openai import OpenAI
import uuid
import openai
import json
import re
import os

with open('/Users/dhiveshakilan/Learning/Python/AI/IntelliAISupport/key.json') as f:
    key=json.load(f)

os.environ["OPENAI_API_KEY"] = key['API_KEY']

file_path= '/Users/dhiveshakilan/Learning/Python/AI/IntelliAISupport/Info Doc/'

# List of PDF files
pdf_files = ['AMGEO.pdf','Eliot.pdf','Error.pdf','Ole_feeding.pdf','role_access.pdf', 'gop_access.pdf','XDS.pdf']
# , 'Sample_schema.pdf']
            #  ,'Table_schema_dict.pdf']  # Add more PDF paths as needed

# Concatenate all the content from multiple PDFs
raw_text = ''

# Loop through each PDF file

for pdf_file in pdf_files:
    pdf = file_path+pdf_file
    pdfreader = PdfReader(pdf)

    # Read and extract text from each page in the PDF
    for i, page in enumerate(pdfreader.pages):
        content = page.extract_text()
        if content:
            raw_text += content

# We need to split the text using Character Text Split such that it sshould not increse token size
text_splitter = CharacterTextSplitter(
    separator = ".",
    chunk_size = 2000,
    chunk_overlap  = 200,
    length_function = len,
)
texts = text_splitter.split_text(raw_text)

# Download embeddings from OpenAI
embeddings = OpenAIEmbeddings()

document_search = FAISS.from_texts(texts, embeddings)

# document_search

chain = load_qa_chain(OpenAI(temperature = 0.2), chain_type="stuff")

app = Flask(__name__)

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
            'IT':{'Gop':{'PDS'},'Perimeter':{'ABD','BCD','KJH'}},
            'TS':{'Gop':{},'Perimeter':{'ABD'}},
            'RD':{'Gop':{'*All*'},'Perimeter':{'BCD','KJH'}}
            }
gop_data = {
        "PDS": {"Perimeter": "ABD","Status": "Active","RDB" : "1234","Zone":"EUR"},
        "XYZ": {"Perimeter": "BCD","Status": "Active","RDB" : "2345","Zone":"USD"},
        "FX": {"Perimeter": "KJH","Status": "Active","RDB" : "3456","Zone":"HK"},
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
            {"Portfolio": "FX-GY-NOMGT", "Status": "Active"},
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

schema_description ='''
Investment Banking Database Model Document
This document outlines the structure and relationships of the database model for tracking underlying securities, products derived from them, and deals made on these products. The database model consists of three main categories of tables: Underlying Tables, Product Tables, and Deal/Trade Tables.
1. Underlying Tables
These tables capture the details of basic financial instruments that can be used to create derivative products.
SHARE Table
Description: Stores information on shares.
Primary Key: share_id
Columns:
share_id (VARCHAR): Unique identifier for each share.
isin (VARCHAR): International Securities Identification Number for the share.
active (TINYINT): Flag indicating if the share is active (1 for active, 0 for inactive).
market_id (VARCHAR): Identifier for the market where the share is traded.
INDEX Table
Description: Stores information on indices.
Primary Key: index_id
Columns:
index_id (VARCHAR): Unique identifier for each index.
active (TINYINT): Flag indicating if the index is active (1 for active, 0 for inactive).
market_id (VARCHAR): Identifier for the market to which the index belongs.

2. Product Tables
Product tables store derivative products based on underlying assets such as shares and indices.
OPTION Table
Description: Stores option contracts, which can be based on shares or indices.
Primary Key: contract_id
Columns:
contract_id (INT): Unique identifier for each option contract.
underlying_id (VARCHAR): Identifier of the underlying asset, referencing either share_id from SHARE table or index_id from INDEX table.
contract_name (VARCHAR): Name of the option contract.
maturity (DATE): Maturity date of the option contract.
type (CHAR): Type of option (C for Call, P for Put).
Relationships:
underlying_id is a foreign key referencing either share_id in SHARE or index_id in INDEX based on the underlying asset.
FUTURE Table
Description: Stores future contracts, which can also be based on shares or indices.
Primary Key: contract_id
Columns:
contract_id (INT): Unique identifier for each future contract.
underlying_id (VARCHAR): Identifier of the underlying asset, referencing either share_id from SHARE table or index_id from INDEX table.
contract_name (VARCHAR): Name of the future contract.
maturity (DATE): Maturity date of the future contract.
Relationships:
underlying_id is a foreign key referencing either share_id in SHARE or index_id in INDEX based on the underlying asset.

3. Deal/Trade Tables
Deal tables store information on trades executed on products or directly on underlying securities. Each trade is versioned, allowing tracking of modifications and deletions.
SECURITY_DEALS Table
Description: Stores details of trades executed directly on shares, without involving derivative products.
Primary Key: deal_id
Columns:
deal_id (INT): Unique identifier for each security trade.
status (CHAR): Status of the trade (I for Initial, R for Recreated/Modified, D for Deleted, C for Cancelled).
date_modified (DATETIME): Timestamp of the most recent modification.
date_st (DATETIME): Timestamp indicating when this version of the trade was stopped. NULL for active trades.
trade_date (DATE): Execution date of the trade.
value_date (DATE): Date when the trade’s value is realized.
trader_id (INT): Identifier for the trader executing the deal.
share_id (VARCHAR): Identifier of the underlying share from the SHARE table.
Relationships:
share_id is a foreign key referencing share_id in the SHARE table.
OPTION_DEALS Table
Description: Stores details of trades executed on options.
Primary Key: deal_id
Columns:
deal_id (INT): Unique identifier for each option trade.
status (CHAR): Status of the trade (same as above).
date_modified (DATETIME): Timestamp of the most recent modification.
date_st (DATETIME): Timestamp indicating when this version of the trade was stopped. NULL for active trades.
trade_date (DATE): Execution date of the trade.
value_date (DATE): Date when the trade’s value is realized.
trader_id (INT): Identifier for the trader executing the deal.
contract_name (VARCHAR): Name of the contract, referencing contract_name in the OPTION table.
Relationships:
contract_name is a foreign key referencing contract_name in the OPTION table.
FUTURE_DEALS Table
Description: Stores details of trades executed on futures.
Primary Key: deal_id
Columns:
deal_id (INT): Unique identifier for each future trade.
status (CHAR): Status of the trade (same as above).
date_modified (DATETIME): Timestamp of the most recent modification.
date_st (DATETIME): Timestamp indicating when this version of the trade was stopped. NULL for active trades.
trade_date (DATE): Execution date of the trade.
value_date (DATE): Date when the trade’s value is realized.
trader_id (INT): Identifier for the trader executing the deal.
contract_name (VARCHAR): Name of the contract, referencing contract_name in the FUTURE table.
Relationships:
contract_name is a foreign key referencing contract_name in the FUTURE table.

Versioning Workflow for Deal Tables
Initial Creation:
When a trade is created, status is set to I.
date_modified captures the creation timestamp.
date_st is set to NULL, indicating the trade is active.
Modification:
When a trade is modified, a new row is created with status set to R.
The previous version’s date_st is updated to the modification timestamp.
The new version has date_modified set to the modification timestamp, with date_st as NULL.
Deletion:
When a trade is deleted, status is changed to D.
The date_st is set to the deletion timestamp.
Querying Active Trades:
Use WHERE date_st IS NULL to retrieve only active trades.
'''

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

def gop_perimeter_check(gop, profile):
    print(gop, profile, gop_perimeter[profile]['Gop'], gop_perimeter[profile])
    
    if profile in gop_perimeter:
        if gop in gop_perimeter[profile]['Gop']:
            return f'{gop} GOP access is already present for profile {profile}.'
        
        else:
            gop_profile = gop_data[gop]['Perimeter']
            act_flg = gop_data[gop]['Status']
            
            if gop_profile in gop_perimeter[profile]['Perimeter']:
                if act_flg == 'Active':
                    return f'Matching GOP: {gop} is available for profile: {profile}.'
                else:
                    return f'{gop} is in {gop_profile} perimeter but is not active.'
            else:
                return f'User with profile {profile} does not have access to the {gop_profile} perimeter for GOP {gop}.'
    
    else:
        return f'No matching profile found for {profile}.'

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def langchain_doc(query):
    docs = document_search.similarity_search(query)
    r=chain.run(input_documents=docs, question=query)
    print('langchain',r)
    return r

# Function to match user query with role keywords using partial matching
def match_role(role, roles_data):
    for i in range(len(roles_data)):
        if role.strip() in roles_data[i]['Role']:
            return f'{roles_data[i]['Role']}'
    return "No matching role found. - No description available"

def find_gop_using_ptf(ptf, ptf_data):
    found_gop=None
    print(ptf)
    for i,j in ptf_data[0].items():
        for k in range(len(j)):
            if j[k]['Portfolio'] in ptf.strip():
                found_gop = i if j[k]["Status"] == "Active" else "Portfolio not active"
                break
    return found_gop if found_gop is not None else "Not found"

def mail(body,subject,sender_email,manager_email,sender_password):
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
    
def counterpart(user_query, counterpart_data):
    # No counterpart Found
    return

# You have not the authorization to perform this action. (technical authorizationn: RUN with discrimnant 'SNIKO' on process group 'EVENT PROCESSING')

def generate_request_id():
    return str(uuid.uuid4())

def role_check(id,role):
    api_url = 'http://127.0.0.1:8080/getrole'
    response = requests.get(api_url)
    if response.status_code == 200:
        user_role = [req for req in response.json() if req.get('user_id') == id]
        for i in user_role:
            if i['role']==role:
                return 'User already have access to this Role'
        return 'No role access given for this user'
    else:
        print(f"Failed to fetch requests: {response.status_code}")
        return []

def gop_check(id,gop):
    api_url = 'http://127.0.0.1:8080/getgop'
    response = requests.get(api_url)
    if response.status_code == 200:
        user_gop = [req for req in response.json() if req.get('user_id') == id]
        for i in user_gop:
            if i['gop']==gop:
                return 'User already have access to this gop'
        return 'No gop access given for this user'
    else:
        print(f"Failed to fetch requests: {response.status_code}")
        return []
    
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
    # content = request.form['content']
    print(f'200 {role}')
    user_id = request.form['userid']
    manager_email = request.form['managerEmail']
    request_id = generate_request_id()
    words_after_colon = re.findall(r':\s*(\w+)', role)
    if 'role' in role.lower() or 'roles' in role.lower():
        print(words_after_colon[0])
        rg = 'role'
        subject = f"Approval Request for {rg} access"
        url=f'https://docs.google.com/forms/d/e/1FAIpQLScC4AvYbx9GIolMmjQQn62mfItYURw0mAZxUEyu4bWHN1ffNQ/viewform?usp=pp_url&entry.1728767546={user_id}&entry.1314294973={request_id}&entry.1971473862={words_after_colon[0]}&entry.1503672414={rg}'
        body = f'''Hello,
            User {user_id} is requesting access to the {words_after_colon[0]} {rg}.
            The request ID for this approval is {request_id}.
            Please review and provide your approval on the below link.
            {url}

            Sincerely,
            Eliot Team'''
        return mail(body,subject,sender_email,manager_email,sender_password)
    elif 'gop' in role.lower() or 'gops' in role.lower() or 'portfolio' in role.lower() or 'portfolios' in role.lower():
        print('gop')
        print(words_after_colon[0],words_after_colon[1])
        rg = 'gop'
        profile=f'{rg}_{words_after_colon[1]}_Profile'
        subject = f"Approval Request for {rg} access"
        url=f'https://docs.google.com/forms/d/e/1FAIpQLScC4AvYbx9GIolMmjQQn62mfItYURw0mAZxUEyu4bWHN1ffNQ/viewform?usp=pp_url&entry.1728767546={user_id}&entry.1314294973={request_id}&entry.1971473862={words_after_colon[0]}&entry.1503672414={profile}'
        body = f'''Hello,
            User {user_id} is requesting access to the {words_after_colon[0]} {rg}.
            The request ID for this approval is {request_id}.
            Please review and provide your approval on the below link.
            {url}

            Sincerely,
            Eliot Team'''
        mail(body,subject,sender_email,manager_email,sender_password)
        team_email = 'dhivesh18122000@gmail.com'
        url2=f'https://docs.google.com/forms/d/e/1FAIpQLScerQ3eeCRDpKobU-jP4x6WsY2XCVUdLJe0YfZEp_wGAkry_A/viewform?usp=pp_url&entry.2116052852={user_id}&entry.1558582620={request_id}&entry.1060472253={words_after_colon[0]}&entry.288713975={words_after_colon[1]}'
        subject = f"Approval Request for {rg} access"
        body2 = f'''Hello,
            Could you please provide approval to add {words_after_colon[0]} {rg} to {words_after_colon[1]} profile.
            Please review and provide your approval on the below link.
            {url2}
            Sincerely,
            Eliot Team'''
        return mail(body2,subject,sender_email,team_email,sender_password)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sql', methods=['POST'])
def generate_response():
    # Get user input from the request
    user_input = request.form.get('textMessage', '')
    print(user_input)
    sql_keywords = ["SQL", "query", "database", "table", "column", "join"]
    if not any(keyword.lower() in user_input.lower() for keyword in sql_keywords):
        return "I don't know"
    
    # If SQL-related, proceed with generating the query
    prompt = f"""
    Database Schema:
    {schema_description}

    User Request: {user_input}
    """
    
    try:
        # Use the updated OpenAI API method for completions
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert in SQL."},
                {"role": "user", "content": prompt}
            ]
        )
        return jsonify({'response_message': completion.choices[0].message.content.strip()})
    
    except Exception as e:
        return jsonify({'response_message': str(e)}), 500

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
        print(matching)
        r = role_check(id,matching)
        if r == 'No role access given for this user':
            response_message = f"Matching Role: {matching}"
            print(response_message)
        else:
            response_message = r
    elif 'portfolio' in text_message.lower() or 'portfolios' in text_message.lower() or 'gop' in text_message.lower() or 'gops' in text_message.lower():
        print('ptf')
        q1 = f"Extract and return only the `portfolio` name from this response: {text_message}. Do not include any other text or formatting."
        matching = find_gop_using_ptf(langchain_doc(q1), ptf_data)
        print(matching)
        r=gop_check(id,matching)
        if matching != "Portfolio not active" and matching != "Not found" and r=='No gop access given for this user':
            print('first print')
            profile_id=account(id)
            if len(profile_id)>1:
                profile = f"{profile_id[1]}"
                print(profile)
                response_message = gop_perimeter_check(matching.strip(),profile)
            else:
                response_message= profile_id[0]
        else: 
            print('gop')
            q = f"Extract and return only the `gop` name from this response: {text_message}. Do not include any other text or formatting."
            matching = langchain_doc(q)
            # q1 = f"Extract and return only the `portfolio` name from this response: {text_message}. Do not include any other text or formatting."
            # matching_ptf = find_gop_using_ptf(langchain_doc(q), gop_data)
            # print(matching_ptf)
            profile_id=account(id)
            print(matching)
            r=gop_check(id,matching)
            if len(profile_id)>1 and r=='No gop access given for this user':
                profile = f"{profile_id[1]}"
                print(profile)
                response_message = gop_perimeter_check(matching.strip(),profile)
            else:
                response_message= profile_id[0]
            # else:
            #     response_message = matching_ptf

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
