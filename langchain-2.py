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
pdf_files = ['AMGEO.pdf','Eliot.pdf','Error.pdf','Ole_feeding.pdf','role_access.pdf', 'gop_access.pdf','XDS.pdf', 'Sample_schema.pdf']
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

chain = load_qa_chain(OpenAI(temperature = 0), chain_type="stuff")

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

# Define the schema description
schema_description = """
Generate an efficient SQL query optimized for large datasets and please don’t change the table names and column names:
1. Table: ACTION - Details about Share.
	⁃	id_titre (String, Primary Key): Unique identifier for each share.
	⁃	id_sous_jacent (Integer): Identifier for the underlying asset.
	⁃	type (String): Type of action.
	⁃	flag_actif (Boolean): Indicates active status of the share.

2. Table: FUND - Details about Fund.
	⁃	id_titre (String, Primary Key): Unique identifier for each fund.
	⁃	id_sous_jacent (Integer): Identifier for the underlying asset.
	⁃	type (String): Type of fund.
	⁃	id_pays (String): Country code for the fund.
	⁃	flag_actif (Boolean): Indicates active status of the fund.
 
3. Table: INDICE - Details about Index.
	⁃	id_indice (String, Primary Key): Unique identifier for each index.
	⁃	id_sous_jacent (Integer): Identifier for the underlying asset.
	⁃	id_marche (String): Market code for the index.
	⁃	id_devise (String): Currency for this index.

4. Table: PANIER - Details about Basket.
	⁃	id_panier (String, Primary Key): Unique identifier for each basket.
	⁃	id_sous_jacent (Integer): Identifier for the underlying asset.
	⁃	id_marche (String): Market code for the basket.
	⁃	id_devise (String): Currency code for the basket.

5. Table: AVMO_TITRE - Details about Regular Market Deals (External Deals).
	⁃	date_saisie (Date): Last modified Date.
	⁃	id_operation (Integer): Deal id.
	⁃	clearer_id_marche (String): Market clearer identifier.
	⁃	clearer_id_compte (String): Clearer's account identifier.
	⁃	id_titre (String): Name of share/fund/warrant. We can join ACTION, FUND, DESC_WARRANT tables.
	⁃	portf_id_tiers (String): Name of portfolio. We can join PORTEFEUILLE table for more information about portfolio.
	⁃	counrtier_id_tiers (String): 
	⁃	id_utilisateur (String): Detail of User/Trader id created for that deal. 
	⁃	sens (String): Buy or Sell information.
	⁃	quantite (Integer): Quantity of the deal.
	⁃	prix (Integer): Unit Price of the Deal.
	⁃	date_operation (Date): Date of the deal created.
	⁃	etat_eng (String): Status of the deal. I - Initial version, R - Revised version, C - Cancelled version, D - Deleted version.
	⁃	date_valeur (Date): Value Date for the deal.
	⁃	date_stop (Date): If date is null then it is active else deal is deleted and date stamp is assigned to this column.

6. Table: ACHAT_VENTE_SO - Details about Clearing Security Deals.
	⁃	date_saisie (Date): Last modified Date.
	⁃	id_operation (Integer): Deal id.
	⁃	countier_id_tiers
	⁃	cash_id_compte
	⁃	id_titre (String): Name of share/fund/warrant. We can join ACTION, FUND, DESC_WARRANT tables.
	⁃	client_id_tiers
	⁃	portf_id_tiers (String): Name of portfolio. We can join PORTEFEUILLE table for more information about portfolio.
	⁃	id_utilisateur (String): Detail of User/Trader id created for that deal. 
	⁃	sens (String): Buy or Sell information.
	⁃	quantite (Integer): Quantity of the deal.
	⁃	prix (Integer): Unit Price of the Deal.
	⁃	date_operation (Date): Date of the deal created.
	⁃	etat_eng (String): Status of the deal. I - Initial version, R - Revised version, C - Cancelled version, D - Deleted version.
	⁃	date_valeur (Date): Value Date for the deal.
	⁃	date_stop (Date): If date is null then it is active else deal is deleted and date stamp is assigned to this column.
	⁃	id_marche (String): Market code for the basket.

7. Table: ACHAT_VENTE_OTC - Details about all OTC deals which involves both Internal and External Deals.
	⁃	date_saisie (Date): Last modified Date.
	⁃	id_operation (Integer): Deal id.
	⁃	prix_id_devise
	⁃	id_utilisateur (String): Detail of User/Trader id created for that deal. 
	⁃	portf_id_tiers (String): Name of portfolio. We can join PORTEFEUILLE table for more information about portfolio.
	⁃	sens (String): Buy or Sell information.
	⁃	quanitie (Integer): Quantity of the deal.
	⁃	prix_unitaire (Integer): Unit Price of the Deal.
	⁃	date_operation (Date): Date of the deal created.
	⁃	etat_eng (String): Status of the deal. I - Initial version, R - Revised version, C - Cancelled version, D - Deleted version.
	⁃	date_valeur (Date): Value Date for the deal.
	⁃	flag_externe (Boolean): if flag is 1 then OTC external deal else OTC Internal Deal.
	⁃	date_stop (Date): If date is null then it is active else deal is deleted and date stamp is assigned to this column.
	⁃	quantite_en_vie (Integer): Remaining Quantity.
	⁃	categorie (String): Category of the Deal.

8. Table: OTC_EXTERNE - Details about External OTC deals.
	⁃	date_saisie (Date): Last modified Date.
	⁃	id_operation (Integer): Deal id.
	⁃	client_id_tiers (String): Counterpart Details.

9. Table: OTC_INTERNE - Details about Internal OTC deals.
	⁃	date_saisie (Date): Last modified Date.
	⁃	id_operation (Integer): Deal id. 
	⁃	id_tiers (String): Name of portfolio. We can join PORTEFEUILLE table for more information about portfolio.

10. Table: CALL_PUT - Details about Contact details
	⁃	nom_contrat
	⁃	strike
	⁃	call_put
	⁃	annee
	⁃	mois 
	⁃	id_valeur

11. Table: META_CALL_PUT 
	⁃	nom_contrat
	⁃	id_sous_jacent
	⁃	id_devise
	⁃	id_marche
	⁃	ame_eurm
	⁃	livraison

12. Table: AVMO_OPTION - Details about Option Deals.
	⁃	date_saisie (Date): Last modified Date.
	⁃	id_operation (Integer): Deal id.
	⁃	nom_contrat (String): 
	⁃	strike (Integer):
	⁃	call_put (String):
	⁃	annee (Integer):
	⁃	mois (Integer):
	⁃	clearer_id_compte
	⁃	portf_id_tiers (String): Name of portfolio. We can join PORTEFEUILLE table for more information about portfolio.
	⁃	countier_id_tiers
	⁃	id_utilisateur (String): Detail of User/Trader id created for that deal. 
	⁃	sensm quantite 
	⁃	prix (Integer): Unit Price of the Deal.
	⁃	date_operation (Date): Date of the deal created.
	⁃	etat_eng (String): Status of the deal. I - Initial version, R - Revised version, C - Cancelled version, D - Deleted version.
	⁃	date_valeur (Date): Value Date for the deal.
	⁃	date_stop (Date): If date is null then it is active else deal is deleted and date stamp is assigned to this column.

13. Table: AVI_VALEUR - Details about Internal Deals.
	⁃	date_saisie (Date): Last modified Date.
	⁃	id_operation (Integer): Deal id.
	⁃	acheteur_id_tiers (String): Name of the Buying Portfolio. We can join PORTEFEUILLE table for more information about portfolio.
	⁃	vendeur_id_tiers (String): Name of the Selling Portfolio. We can join PORTEFEUILLE table for more information about portfolio.
	⁃	id_valeur
	⁃	id_utilisateur (String): Detail of User/Trader id created for that deal. 
	⁃	sens (String): Buy or Sell information.
	⁃	quanitie (Integer): Quantity of the deal.
	⁃	prix_element (Integer): Unit Price of the Deal.
	⁃	date_operation (Date): Date of the deal created.
	⁃	etat_eng (String): Status of the deal. I - Initial version, R - Revised version, C - Cancelled version, D - Deleted version.
	⁃	date_valeur (Date): Value Date for the deal.
	⁃	date_stop (Date): If date is null then it is active else deal is deleted and date stamp is assigned to this column.

28. Table: CENTRE_COMPTABLE - Details about GOP.
	⁃	id_centre (String): Name of the GOP. We can join PORTEFEUILLE table for more information about the portfolios.
	⁃	id_groupe (String): Name of the Group. We can join GROUPE_COMPTABLE table  for more information about the group.
	⁃	nom_place (String):
	⁃	code_bdr (Integer): BDR No. For each gop.
	⁃	date_creation (Date): Creation Date of GOP.
	⁃	id_zone (String): GOP comes under specific Zone like EUR, HK, USD, etc… 
	⁃	flag_actif (Boolean): If flag is 1 then GOP is active else GOP is not active.

29. Table: PORTEFEUILLE - Details about Portfolio.
	⁃	id_tiers (String): Name of the Portfolio.
	⁃	id_centre (String): Name of the GOP. We can join CENTRE_COMPTABLE table for more information about the GOP.
	⁃	date_creation (Date): Creation Date of Portfolio.

30. Table: GROUPE_COMPTABLE - Details about Group.
	⁃	id_groupe (String): Name of the group. We can join CENTRE_COMPTABLE table  for more information about the gop.
	⁃	id_societe (String): Name of the Societe. We can join SOCIETE table for more information about the Societe.
	⁃	id_devise (String): Currency of the Group.
	⁃	libelle (String):
	⁃	code_SG (Integer):

31. Table: SOCIETE - Details about Societe.
	⁃	id_societe (String): Name of the Societe. We can join GROUPE_COMPTABLE for more information about the group.
	⁃	libelle (String): 
	⁃	code_societe (Integer):
	⁃	code_bdr (Integer): BDR number.
	⁃	id_devise (String): Currency of the Societe.
	⁃	nationalite (String): Zone of the Societe.

32. Table: UTILISATEUR - Details about User/Trader.
	⁃	id_utilisateur (Integer): user login id.
	⁃	nom (String): Last Name.
	⁃	prenom (String): First Name
	⁃	email (String): user mail id.
	⁃	sesame_id (String): windows id.

36. Table: DESC_WARRANT - Details about Warrant.
	⁃	id_titre (String, Primary Key): Unique identifier for each warrant.
	⁃	date_saisie (Date): Last modified Date.
	⁃	id_def
	⁃	id_clp
	⁃	date_stop (Date): If date is null then it is active else deal is deleted and date stamp is assigned to this column.
	⁃	categorie (String): Category of the Deal.
	⁃	id_produit_sales

41. Table: SORTIE_GENERIQUE - Details about Eole Feeding Deals (It will get purged after 5 days, if you want to see this deal then you need to Resend the deal).

42. Table: VALEUR_MOBILIERE 
	⁃	id_titre 
	⁃	id_marche 
	⁃	id_valeur 
	⁃	id_societe 
	⁃	emis_en_id_devise

Assumptions: 
- Assume columns with similar names may represent relationships.

Key Requirements for Queries:
1. Always use indexed columns for filtering and joins.
2. Avoid using SELECT *; specify required columns.
3. Optimize date range queries and aggregations.
4. Use LIMIT to restrict the result set when appropriate.
5. Ensure queries are efficient for handling large datasets.
"""

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

def langchain_doc(query):
    docs = document_search.similarity_search(query)
    r=chain.run(input_documents=docs, question=query)
    return r

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

@app.route('/sql', methods=['POST'])
def generate_response():
    # Initialize the OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # Get user input and generate response
    user_input = request.form.get('textMessage', '')
    # Define keywords to identify SQL and technical questions
    sql_keywords = ["SQL", "query", "database", "table", "column", "join"]
    tech_keywords = ["code", "program", "python", "java", "function", "variable", "loop", "class", "object"]

    # Check if input is SQL-related
    if any(keyword.lower() in user_input.lower() for keyword in sql_keywords):
        prompt = f"""
        Database Schema:
        {schema_description}

        User Request: {user_input}
        """
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert in SQL."},
                {"role": "user", "content": prompt}
            ]
        )
        return jsonify({'response_message': completion.choices[0].message.content.strip()})

    # Check if input is a technical question
    elif any(keyword.lower() in user_input.lower() for keyword in tech_keywords):
        tech_prompt = f"Answer the following technical question:\n\n{user_input}"
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert in technology and programming."},
                {"role": "user", "content": tech_prompt}
            ]
        )
        return jsonify({'response_message': completion.choices[0].message.content.strip()})
    # If neither, return a default response
    else:
        return jsonify({'response_message': "I don't know"})

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
