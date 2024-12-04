# Import necessary modules from LangChain and other libraries
from langchain_community.document_loaders import PyPDFLoader  # For loading PDFs
from langchain.schema import Document  # To work with Document schema in LangChain
from langchain_community.embeddings import OpenAIEmbeddings  # For embedding text with OpenAI
from langchain.chains import create_retrieval_chain  # For creating a retrieval chain from documents
from langchain.chains.combine_documents import create_stuff_documents_chain  # Combine document chains
from langchain_core.prompts import ChatPromptTemplate  # For creating prompt templates for chats
from langchain.chains import LLMChain  # For chaining LLMs with LangChain
from langchain.prompts import PromptTemplate  # For defining prompt templates
from langchain_community.vectorstores import FAISS  # FAISS for vector storage
from langchain.chat_models import ChatOpenAI  # OpenAI Chat model integration
from langchain.text_splitter import RecursiveCharacterTextSplitter  # For splitting long text into smaller chunks
from langchain.vectorstores import FAISS  # Import FAISS again for vector storage
from langchain.memory import ConversationBufferMemory  # For memory during conversations
from flask import Flask, request, jsonify, render_template, session  # Flask for web app
import base64  # For encoding/decoding data
import requests  # For making HTTP requests
import smtplib  # For sending emails
from email.mime.text import MIMEText  # For creating email content
import uuid  # For generating unique IDs
import json  # For handling JSON data
import re  # For regex operations
import os  # For handling file paths and environment variables

# Load the API key and other sensitive data from a local JSON file
with open('/Users/dhiveshakilan/Learning/Python/AI/IntelliAISupport/key.json') as f:
    key = json.load(f)  # Load the JSON data from the file

# Set OpenAI API key from the loaded key data
os.environ["OPENAI_API_KEY"] = key['API_KEY']
OWNER = key['OWNER']  # GitHub repository owner
REPO = key['REPO']  # GitHub repository name
GITHUB_TOKEN = key['GITHUB_TOKEN']  # GitHub token for API access

# Define the file path where PDF files are stored
file_path = '/Users/dhiveshakilan/Learning/Python/AI/IntelliAISupport/Info_Doc/'

# List of PDF files to be loaded and processed
pdf_files = ['AMGEO.pdf', 'role_access.pdf', 'gop_access.pdf', 'XDS.pdf']

# Initialize a list to store document objects
docs = []

# Load each PDF and convert the pages into document objects
for pdf_file in pdf_files:
    pdf = file_path + pdf_file  # Full path to the PDF file
    
    # Load the PDF using PyPDFLoader
    loader = PyPDFLoader(pdf)
    
    # Extract pages from the PDF
    pages = loader.load()

    # Convert each page into a Document object and append to the docs list
    for page in pages:
        document = Document(page_content=page.page_content)  # Create a Document object
        docs.append(document)

# Split the loaded documents into smaller chunks to avoid exceeding token limits for LLMs
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)  # Specify chunk size and overlap
documents = text_splitter.split_documents(docs)  # Split documents

# Initialize the FAISS vector store with OpenAI embeddings for document retrieval
db = FAISS.from_documents(documents[:30], OpenAIEmbeddings())  # Use the first 30 documents for the vector store

# Initialize the OpenAI Chat model (GPT-4 Mini) with a low temperature for less random responses
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# Set up memory for the conversation (e.g., to maintain context during a chat)
memory = ConversationBufferMemory(memory_key="chat_history")

# Initialize the Flask web app
app = Flask(__name__)
app.secret_key = key['SECRET_KEY']  # Set a secret key for session management

# Function to get account details for a given user ID
def account(id):
    # Define the API endpoint to fetch account details
    api_url = 'http://127.0.0.1:8080/getaccount'
    # Send a GET request with the user ID as a parameter
    response = requests.get(api_url, params={'id': id})
    
    # Check if the response is successful (status code 200)
    if response.status_code == 200:
        user_account = response.json()  # Parse the JSON response
        
        # Check if the account is active
        if user_account[0]['active'] == True:
            profile = user_account[0]['profile']  # Get the profile of the active account
            return ['Account is active', profile]
        else:
            return ['Account is not active.']
    else:
        print("Failed to fetch data. Status code:", response.status_code)

# Function to check the GOP perimeter for a given PTF and profile
def ptf_perimeter_check(ptf, profile):
    api_url_get_gop_using_ptf = 'http://127.0.0.1:8080/get_gop_using_ptf'
    
    # Send a GET request to fetch the GOP using the provided PTF
    get_gop_using_ptf_response = requests.get(api_url_get_gop_using_ptf, params={'ptf': ptf})
    
    if get_gop_using_ptf_response.status_code == 200:
        get_gop_using_ptf = get_gop_using_ptf_response.json()
        gop = get_gop_using_ptf[0]
        return gop_perimeter_check(gop, profile)  # Call another function to check GOP perimeter
    else:
        print("Failed to fetch data. Status code:", get_gop_using_ptf_response.status_code)

# Function to check the GOP access and perimeter details
def gop_perimeter_check(gop, profile):
    api_url_gop_perimeter = 'http://127.0.0.1:8080/gop_check_in_perimeter'
    api_url_gop_data = 'http://127.0.0.1:8080/gop_data'
    
    # Check if the GOP is in the specified perimeter
    gop_check_in_perimeter_response = requests.get(api_url_gop_perimeter, params={'profile': profile})
    gop_data_response = requests.get(api_url_gop_data, params={'gop': gop})

    # If the request is successful
    if gop_check_in_perimeter_response.status_code == 200:
        gop_check_in_perimeter = gop_check_in_perimeter_response.json() 
        # Check if GOP exists in perimeter
        if gop in gop_check_in_perimeter:
            return f'{gop} GOP access is already present for profile {profile}.'
        else:
            # Fetch perimeter and status details if not found in perimeter
            api_url_gop_perimeter = 'http://127.0.0.1:8080/gop_perimeter'    
            gop_perimeter_response = requests.get(api_url_gop_perimeter, params={'profile': profile})
            if gop_perimeter_response.status_code == 200 and gop_data_response.status_code == 200:
                gop_perimeter = gop_perimeter_response.json()
                gop_data = gop_data_response.json()
                gop_profile = gop_data[0]['perimeter']
                act_flg = gop_data[0]['status']
                
                # Check if the user has access to the perimeter and the status of the GOP
                if gop_profile in gop_perimeter:
                    if act_flg == 'Active':
                        return f'Matching GOP: {gop} is available for profile: {profile}.'
                    else:
                        return f'{gop} is in {gop_profile} perimeter but is not active.'
                else:
                    return f'User with profile {profile} does not have access to the {gop_profile} perimeter for GOP {gop}.'
            else:
                print("Failed to fetch data. Status code:", gop_perimeter_response.status_code)
    else:
        print("Failed to fetch data. Status code:", gop_check_in_perimeter_response.status_code)

# Function to encode an image to base64 format
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# LangChain document-based query function
def langchain_doc(query):
    # Design ChatPrompt Template for LangChain
    prompt = ChatPromptTemplate.from_template("""
    Answer the following question based only on the provided context. 
    Think step by step before providing a detailed answer. 
    <context>
    {context}
    </context>
    Question: {input}""")

    # Create Stuff Document Chain to handle document-based queries
    document_chain = create_stuff_documents_chain(llm, prompt)
    
    # Set up a retriever for the FAISS vector store
    retriever = db.as_retriever()
    
    # Create the retrieval chain
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    
    # Execute the retrieval chain with the input query
    response = retrieval_chain.invoke({"input": query})
    print('langchain', response['answer'])
    return response['answer']

# Function to match a role with role keywords using partial matching
def match_role(role):
    # Fetch matching roles from the API
    api_url_get_matching_role = 'http://127.0.0.1:8080/get_matching_role'
    get_matching_role_response = requests.get(api_url_get_matching_role)
    # Check if the role is found in the list of matching roles
    if role.strip() in get_matching_role_response.json():
        return role.strip()
    return "No matching role found. - No description available"

# Function to find GOP associated with a PTF
def find_gop_using_ptf(ptf):
    found_gop = None
    # Fetch PTF data from the API
    api_url_get_ptf = 'http://127.0.0.1:8080/get_ptf'
    get_ptf_response = requests.get(api_url_get_ptf, params={'ptf': ptf})

    if get_ptf_response.status_code == 200:
        get_ptf = get_ptf_response.json()
        # Check if the PTF is active or not
        if get_ptf[0] == "Active":
            found_gop = ptf
        elif get_ptf[0] == "Not Active":
            found_gop = "Portfolio not active"
    
    return found_gop if found_gop is not None else "Not found"

# Function to send an email (e.g., for approval notifications)
def mail(body, subject, sender_email, manager_email, sender_password):
    msg = MIMEText(body)  # Create MIMEText email message
    msg['Subject'] = subject  # Set email subject
    msg['From'] = sender_email  # Set sender email
    msg['To'] = manager_email  # Set recipient email

    try:
        # Establish SMTP connection and send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # Start TLS encryption
            server.login(sender_email, sender_password)  # Login to the email server
            server.send_message(msg)  # Send the message
        return jsonify({'status': 'success', 'message': 'Approval email sent successfully.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
    
# Function to generate a unique request ID
def generate_request_id():
    return str(uuid.uuid4())

# Function to check if a user already has a specific role
def role_check(id, role):
    api_url = 'http://127.0.0.1:8080/getrole'
    response = requests.get(api_url)
    
    if response.status_code == 200:
        user_role = [req for req in response.json() if req.get('user_id') == id]
        # Check if the user already has the specified role
        for i in user_role:
            if i['role'] == role:
                return 'User already has access to this Role'
        return 'No role access given for this user'
    else:
        print(f"Failed to fetch requests: {response.status_code}")
        return []

# Function to check if a user has access to a specific GOP
def gop_check(id, gop):
    api_url = 'http://127.0.0.1:8080/getgop'
    response = requests.get(api_url)
    
    if response.status_code == 200:
        user_gop = [req for req in response.json() if req.get('user_id') == id]
        # Check if the user already has the specified GOP access
        for i in user_gop:
            if i['gop_name'] == gop:
                return 'User already has access to this GOP'
        return 'No GOP access given for this user'
    else:
        print(f"Failed to fetch requests: {response.status_code}")
        return []

# Define custom prompt template for SQL generation
sql_prompt_template = """
Given the following database schema: {schema_description},
Generate a SQL query to answer the following question:
{question}
Please ensure the query is correct and formatted properly.
Use previous responses to refine the query if needed: 
Previous User Message: 
{previous_user_message}

Previous Assistant Response: 
{previous_llm_response}
"""

# Function to create an SQL query chain with memory
def create_sql_query_chain():
    prompt = PromptTemplate(input_variables=["question", "schema_description", "previous_sql_query"], template=sql_prompt_template)
    sql_chain = LLMChain(prompt=prompt, llm=llm)
    return sql_chain

# Initialize the SQL query chain
sql_query_chain = create_sql_query_chain()

# Load schema description from the PDF file
loader = PyPDFLoader("/Users/dhiveshakilan/Learning/Python/AI/IntelliAISupport/Info_Doc/schema.pdf")
schema_description = loader.load()

@app.route('/')
def index():
    return render_template('index.html')

# /text - Any text response calls this end point and give a response
@app.route('/text', methods=['POST'])
def text():
    text_response = request.form.get('textMessage', '')
    k = langchain_doc(text_response)
    print(k)
    return jsonify({'response_message': k})

# /send_email - send approval mail request for role/GOP access
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

def github(PATTERN):
    # GitHub API URL to get the repository contents
    repo_url = f'https://api.github.com/repos/{OWNER}/{REPO}/contents'

    # Send the GET request to fetch the repository contents
    response = requests.get(repo_url, headers={'Authorization': f'token {GITHUB_TOKEN}'})

    # Check if the connection to GitHub was successful
    if response.status_code == 200:
        print(f"Connection to GITHUB successful!, {PATTERN}")
        repo_contents = response.json()  # Parse the response as JSON to get the repository contents
        
        # Iterate over the contents and print files that match the pattern
        for content in repo_contents:
            # Check if the file name starts with the specified pattern
            if content['name'].startswith(PATTERN):  # Match files that start with the specified pattern (e.g., 'OLE')
                print(f"Match found: {content['name']}")
                
                # Get the content of the matched file
                file_url = content['url']  # URL to get the file details
                file_response = requests.get(file_url, headers={'Authorization': f'token {GITHUB_TOKEN}'})
                
                # Check if the file content was successfully fetched
                if file_response.status_code == 200:
                    file_data = file_response.json()  # Parse the response as JSON
                    
                    # The file content is base64 encoded, so decode it
                    encoded_content = file_data['content']  # Get the base64 encoded content
                    decoded_content = base64.b64decode(encoded_content).decode('utf-8')  # Decode the content
                    return decoded_content  # Return the decoded content
                else:
                    # If unable to fetch the file content, return the error message with the status code
                    return f"Failed to fetch the content of {content['name']}. Status code: {file_response.status_code}"
    else:
        # If unable to connect to the GitHub repository, return the error message with the status code
        return f"Failed to connect to the repository. Status code: {response.status_code}"
    
    return 'No file found'  # Return message if no matching file is found

@app.route('/debug_user_query', methods=['POST'])
def debug_user_query():
    text_response = request.form.get('textMessage', '')
    print(text_response)

    # End chat if the user says "no"
    if text_response.lower() == "no":
        session.pop('chat_history', None)
        print(session)
        return jsonify({'response_message': "You have switched to general queries."})

    deal_prompt = f'Give me only the deal id from this response (only number) - {text_response}'
    sql_file_response = f'Give me the stored procedure name (like ole, goat, etc..) from user response (only name) - {text_response}'
    sql_file = llm.predict(sql_file_response)
    stored_proc = github(sql_file)
    print(stored_proc)

    deal_id = llm.predict(deal_prompt)
    try:
        deal_id = int(deal_id)
    except ValueError:
        deal_id = None

    # Condition 1: No file found & no previous chat history
    if stored_proc in ['No file found', 'Failed to connect to the repository.', 'Failed to fetch the content'] and 'chat_history' not in session:
        return jsonify({'response_message': "No file found."})

    # Condition 2: No deal ID & no file name found, but chat history exists
    if deal_id is None and stored_proc in ['No file found', 'Failed to connect to the repository.', 'Failed to fetch the content']:
        if 'chat_history' in session:
            return handle_previous_chat_response(text_response)

    # Condition 3: No deal ID, but file name is found, and chat history exists
    if deal_id is None and stored_proc not in ['No file found', 'Failed to connect to the repository.', 'Failed to fetch the content']:
        if 'chat_history' in session:
            return handle_previous_chat_response(text_response)

    # Condition 4: Deal ID is present, but no file name, with chat history
    if stored_proc in ['No file found', 'Failed to connect to the repository.', 'Failed to fetch the content']:
        return handle_previous_chat_response(text_response)

    # Proceed if deal_id and stored_proc are present
    api_url = 'http://127.0.0.1:8080/goat'
    response = requests.get(api_url, params={'deal_id': deal_id})
    
    if response.status_code == 200:
        query = response.json()
    else:
        query = {'data': f'Failed to fetch requests: {response.status_code}'}
    
    print(query['data'])

    if 'chat_history' not in session:
        session['chat_history'] = [{"role": "system", "content": "You are an expert in debugging stored procedures."}]
    
    session['chat_history'].append({"role": "user", "content": text_response})

    if 'chat_history' in session and len(session['chat_history']) > 2:
        previous_user_message = session['chat_history'][-2]['content']
        previous_llm_response = session['chat_history'][-1]['content']
    else:
        previous_user_message = "No prior response available."
        previous_llm_response = "No prior response available."

    prompt = f"""
    Stored Procedure:
    {stored_proc}

    User Request: {text_response}

    Previous User Message: 
    {previous_user_message}

    Previous Assistant Response: 
    {previous_llm_response}

    Debug the stored procedure based on the below results and give precise functional details by considering the comments in the code. Avoid technical details.

    {query['data']}
    """

    completion = llm.predict(f"You are an expert in debugging stored procedures.\n{prompt}")
    session['chat_history'].append({"role": "assistant", "content": completion.strip()})
    print(session)
    return jsonify({'response_message': completion.strip()})

def handle_previous_chat_response(text_response):
    previous_assistant_response = ""  # Initialize an empty string for previous assistant's response

    # Check if there is chat history and the length of chat history is greater than 2 (i.e., at least two messages)
    if 'chat_history' in session and len(session['chat_history']) > 2:
        # Retrieve the previous user message and the previous assistant's response from the chat history
        previous_user_message = session['chat_history'][-2]['content']
        previous_llm_response = session['chat_history'][-1]['content']
    else:
        # If chat history doesn't exist or is too short, assign default messages
        previous_user_message = "No prior response available."
        previous_llm_response = "No prior response available."

    # Debug: Print the previous assistant's response (initially empty)
    print(f"handle_previous_chat_response'{previous_assistant_response}")

    # Prepare the prompt with prior conversation context
    prompt = f"""
You are an expert in answering based on prior context.

Previous User Message: 
{previous_user_message}

Previous Assistant Response: 
{previous_llm_response}

User Request: 
{text_response}

Please provide an updated response considering the above context.
"""
    # Pass the constructed prompt to the language model to generate a response
    completion = llm.predict(f"You are an expert in answering questions from previous chat history.\n{prompt}")
    
    # Append the assistant's new response to the session's chat history
    session['chat_history'].append({"role": "assistant", "content": completion.strip()})
    
    # Return the response message in JSON format
    return jsonify({'response_message': completion.strip()})

# /sql - Any sql generation will be handled by this end point
@app.route('/sql', methods=['POST'])
def generate_response():
    user_input = request.form.get('textMessage', '')
    
    # Initialize chat history if not present
    if 'chat_history' not in session:
        session['chat_history'] = [{"role": "system", "content": "You are an expert in SQL. Please refer to the provided schema for all questions."}]
    
    # End chat if the user says "no"
    if user_input.lower() == "no":
        session.pop('chat_history', None)
        return jsonify({'response_message': "You have switched to general queries."})
    
    # Add the user's query to the session history
    session['chat_history'].append({"role": "user", "content": user_input})
    
    # Retrieve the previous SQL query from memory (if any)
    if 'chat_history' in session and len(session['chat_history']) > 2:
        previous_user_message = session['chat_history'][-2]['content']
        previous_llm_response = session['chat_history'][-1]['content']
    else:
        previous_user_message = "No prior response available."
        previous_llm_response = "No prior response available."

    print(session['chat_history'])
    # Use the SQL query chain to generate the SQL
    sql_query = sql_query_chain.run({
        "question": user_input,
        "schema_description": schema_description,
        "previous_user_message": previous_user_message,
        "previous_llm_response": previous_llm_response
    })

    # Add the assistant's SQL query to the session history
    session['chat_history'].append({"role": "assistant", "content": sql_query})

    # Return the generated SQL query as a response
    return jsonify({'response_message': sql_query})

# /image_to_text - It converts image reponse to text and calls /text
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

# /text_to_role - Validations on access role/GOP
@app.route('/text_to_role', methods=['POST'])
def text_to_role():
    id = request.form.get('userid', '')
    text_message = request.form.get('textMessage', '')
    print(text_message)
    if not text_message:
        return jsonify({"error": "No text message provided"}), 400

    # query = "Why I am getting this message - "+text_message
    if 'role' in text_message.lower() or 'roles' in text_message.lower():
        q = f"Only return the role name from this response (one word answer): {text_message}"
        matching = match_role(langchain_doc(q))
        print(matching)
        if matching != "No matching role found. - No description available":
            r = role_check(id,matching)
            if r == 'No role access given for this user':
                response_message = f"Matching Role: {matching}"
                print(response_message)
            else:
                response_message = r
        else:
            response_message = matching
    elif 'portfolio' in text_message.lower() or 'portfolios' in text_message.lower() or 'gop' in text_message.lower() or 'gops' in text_message.lower():
        print('ptf')
        q1 = f"Extract and return only the `portfolio` name from this response (one word answer): {text_message}. Do not include any other text or formatting."
        matching = find_gop_using_ptf(langchain_doc(q1).strip())
        print(matching)
        r=gop_check(id,matching.strip())
        if matching != "Portfolio not active" and matching != "Not found" and r=='No gop access given for this user':
            print('first print')
            profile_id=account(id)
            if len(profile_id)>1:
                profile = f"{profile_id[1]}"
                print(profile)
                response_message = ptf_perimeter_check(matching.strip(),profile)
            else:
                if r!='No gop access given for this user':
                    response_message = r
                else:
                    response_message= profile_id[0]
        else: 
            print('gop')
            q = f"Extract and return only the `gop` name from this response (one word answer): {text_message}. Do not include any other text or formatting."
            matching = langchain_doc(q)
            profile_id=account(id)
            print(matching)
            r=gop_check(id,matching.strip())
            if len(profile_id)>1 and r=='No gop access given for this user':
                profile = f"{profile_id[1]}"
                print(profile)
                response_message = gop_perimeter_check(matching.strip(),profile)
            else:
                if r!='No gop access given for this user':
                    response_message = r
                else:
                    response_message= profile_id[0]        
    else:
        response_message = f"{text_message}"
    print(response_message)

    return jsonify({
        "extracted_message": text_message,
        "response_message": response_message
    })

if __name__ == '__main__':
    app.run(debug=True)
