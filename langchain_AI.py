from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import Document
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from flask import Flask, request, jsonify, render_template, session
import base64
import requests
import smtplib
from email.mime.text import MIMEText
import uuid
import json
import re
import os

with open('/Users/dhiveshakilan/Learning/Python/AI/IntelliAISupport/key.json') as f:
    key=json.load(f)

os.environ["OPENAI_API_KEY"] = key['API_KEY']
OWNER = key['OWNER']
REPO = key['REPO']
GITHUB_TOKEN = key['GITHUB_TOKEN']

file_path= '/Users/dhiveshakilan/Learning/Python/AI/IntelliAISupport/Info_Doc/'

# List of PDF files
pdf_files = ['AMGEO.pdf','role_access.pdf','gop_access.pdf','XDS.pdf']

# Initialize a list to store documents
docs = []

# Use PyPDFLoader to load each PDF
for pdf_file in pdf_files:
    pdf = file_path + pdf_file
    
    # Load the PDF using PyPDFLoader
    loader = PyPDFLoader(pdf)
    
    # Extract text from the PDF pages
    pages = loader.load()

    # Convert pages to Document objects (if not already in that format)
    for page in pages:
        document = Document(page_content=page.page_content)  # Create a document object
        docs.append(document)

# We need to split the text using Character Text Split such that it sshould not increse token size
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
documents=text_splitter.split_documents(docs)

db=FAISS.from_documents(documents[:30],OpenAIEmbeddings())

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
# Initialize ConversationBufferMemory
memory = ConversationBufferMemory(memory_key="chat_history")

app = Flask(__name__)
app.secret_key = key['SECRET_KEY']


def account(id):
    api_url = 'http://127.0.0.1:8080/getaccount'
    response = requests.get(api_url, params={'id': id})
    if response.status_code == 200:
        user_account=response.json()
        if user_account[0]['active']== True:
            profile = user_account[0]['profile']
            # print(f'Profile {profile}')
            return ['Account is active' , profile]
        # elif user_account['active']== '1':
        #     return ['Account is not active.']
        else:
            return ['Account is not active.']
            # return ['No user id found.']
    else:
        print("Failed to fetch data. Status code:", response.status_code)

def ptf_perimeter_check(ptf,profile):
    api_url_get_gop_using_ptf = 'http://127.0.0.1:8080/get_gop_using_ptf'
    get_gop_using_ptf_response = requests.get(api_url_get_gop_using_ptf, params={'ptf': ptf})
    if get_gop_using_ptf_response.status_code == 200:
        get_gop_using_ptf = get_gop_using_ptf_response.json()
        gop = get_gop_using_ptf[0]
        return gop_perimeter_check(gop,profile)
    else:
        print("Failed to fetch data. Status code:", get_gop_using_ptf_response.status_code)

def gop_perimeter_check(gop, profile):
    api_url_gop_perimeter = 'http://127.0.0.1:8080/gop_check_in_perimeter'
    api_url_gop_data = 'http://127.0.0.1:8080/gop_data'
    gop_check_in_perimeter_response = requests.get(api_url_gop_perimeter, params={'profile': profile})
    gop_data_response = requests.get(api_url_gop_data, params={'gop': gop})

    if gop_check_in_perimeter_response.status_code == 200:
        gop_check_in_perimeter = gop_check_in_perimeter_response.json() 
        if gop in gop_check_in_perimeter:
                return f'{gop} GOP access is already present for profile {profile}.'
        else:
            api_url_gop_perimeter = 'http://127.0.0.1:8080/gop_perimeter'    
            gop_perimeter_response = requests.get(api_url_gop_perimeter, params={'profile': profile})
            if gop_perimeter_response.status_code == 200 and gop_data_response.status_code == 200:
                gop_perimeter= gop_perimeter_response.json()
                gop_data = gop_data_response.json()
                gop_profile = gop_data[0]['perimeter']
                act_flg = gop_data[0]['status']
                
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

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def langchain_doc(query):
    ## Design ChatPrompt Template
    prompt = ChatPromptTemplate.from_template("""
    Answer the following question based only on the provided context. 
    Think step by step before providing a detailed answer. 
    <context>
    {context}
    </context>
    Question: {input}""")

    ## Chain Introduction
    ## Create Stuff Docment Chainy)
    document_chain=create_stuff_documents_chain(llm,prompt)
    retriever=db.as_retriever()
    retrieval_chain=create_retrieval_chain(retriever,document_chain)
    response=retrieval_chain.invoke({"input":query})
    print('langchain',response['answer'])
    return response['answer']

# Function to match user query with role keywords using partial matching
def match_role(role):
    api_url_get_matching_role = 'http://127.0.0.1:8080/get_matching_role'
    get_matching_role_response = requests.get(api_url_get_matching_role)
    print(role,get_matching_role_response)
    if role.strip() in get_matching_role_response.json():
        return role.strip()
    return "No matching role found. - No description available"

def find_gop_using_ptf(ptf):
    found_gop=None
    api_url_get_ptf = 'http://127.0.0.1:8080/get_ptf'
    get_ptf_response = requests.get(api_url_get_ptf, params={'ptf': ptf})

    if get_ptf_response.status_code == 200:
        print(get_ptf_response.json())
        get_ptf = get_ptf_response.json()
        if get_ptf[0]== "Active":
            found_gop = ptf
        elif get_ptf[0]== "Not Active":
            found_gop = "Portfolio not active"
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
        print(user_gop)
        for i in user_gop:
            if i['gop_name']==gop:
                return 'User already have access to this gop'
        return 'No gop access given for this user'
    else:
        print(f"Failed to fetch requests: {response.status_code}")
        return []
    
# Define custom prompt template for SQL generation
sql_prompt_template = """
Given the following database schema: {schema_description},
Generate a SQL query to answer the following question:
{question}
Please ensure the query is correct and formatted properly.
Use previous responses to refine the query if needed: {previous_sql_query}
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

    if response.status_code == 200:
        print(f"Connection GITHUB successful!, {PATTERN}")
        repo_contents = response.json()
        
        # Iterate over the contents and print files that match the pattern
        for content in repo_contents:
            if content['name'].startswith(PATTERN):  # Match files that start with 'OLE'
                print(f"Match found: {content['name']}")
                
                # Get the content of the matched file
                file_url = content['url']  # URL to get the file details
                file_response = requests.get(file_url, headers={'Authorization': f'token {GITHUB_TOKEN}'})
                
                if file_response.status_code == 200:
                    file_data = file_response.json()
                    
                    # The file content is base64 encoded
                    encoded_content = file_data['content']
                    decoded_content = base64.b64decode(encoded_content).decode('utf-8')  # Decode the content
                    return decoded_content
                else:
                    return f"Failed to fetch the content of {content['name']}. Status code: {file_response.status_code}"
    else:
        return f"Failed to connect to the repository. Status code: {response.status_code}"
    return 'No file found'

# /debug_user_query - Debug the stored proc based on the user request
@app.route('/debug_user_query', methods=['POST'])
def debug_user_query():
    text_response = request.form.get('textMessage', '')
    print(text_response)

    # # End chat if the user says "no"
    if text_response.lower() == "no":
        session.pop('chat_history', None)
        return jsonify({'response_message': "You have switched to general queries."})

    deal_prompt = f'Give me only the deal id from this response (only number) - {text_response}'
    sql_file_response = f'Give me the stored procedure name (like ole, goat, etc..) from user response (only name) - {text_response}'
    sql_file = llm.predict(sql_file_response)
    stored_proc = github(sql_file)
    print(stored_proc)
    
    if stored_proc in ['No file found', 'Failed to connect to the repository.', 'Failed to fetch the content'] or ('chat_history' not in session):
        return jsonify({'response_message': stored_proc})
    else:
        # If deal_id is not found, provide a default response based on the chat history
        deal_id = llm.predict(deal_prompt)
        print(deal_id)

        try:
            deal_id = int(deal_id)  # Convert deal_id to an integer
        except ValueError:
            deal_id = None  # If it's not an integer, set deal_id to None and continue

        if deal_id is None:
            # Handle the case where no deal_id is provided; you can add logic here for fallback
            # For example, you can use a default message or proceed without the deal_id
            print("No deal_id provided, continuing conversation based on previous context.")

            # Initialize chat history if not present
            if 'chat_history' not in session:
                session['chat_history'] = [{"role": "system", "content": "You are an expert in debugging stored procedures."}]
            
            # Add the user's query to the session history
            session['chat_history'].append({"role": "user", "content": text_response})

            # Retrieve the previous assistant response (if any)
            previous_assistant_response = ""
            if len(session['chat_history']) > 1:
                previous_assistant_response = session['chat_history'][-3]['content']
            
            # Construct the prompt for the LLM, even if deal_id is not present
            prompt = f"""
            Stored Procedure:
            {stored_proc}

            User Request: {text_response}

            Previous Assistant Response: {previous_assistant_response}

            Debug the stored procedure based on the below results and give precise functional details by considering the comments in the code. Avoid technical details.
            """
            
            # Use LangChain's LLMChain to process the prompt
            completion = llm.predict(f"You are an expert in debugging stored procedures.\n{prompt}")

            # Add the assistant's response to the session history
            session['chat_history'].append({"role": "assistant", "content": completion.strip()})

            return jsonify({'response_message': completion.strip()})
        
        else:
            api_url = 'http://127.0.0.1:8080/goat'
            response = requests.get(api_url, params={'deal_id': deal_id})
            
            if response.status_code == 200:
                query = response.json()
            else:
                query = {'data': f'Failed to fetch requests: {response.status_code}'}
            
            print(query['data'])

            # Initialize chat history if not present
            if 'chat_history' not in session:
                session['chat_history'] = [{"role": "system", "content": "You are an expert in debugging stored procedures."}]
            
            # # Add the user's query to the session history
            session['chat_history'].append({"role": "user", "content": text_response})
            
            # # Retrieve the previous assistant response (if any)
            previous_assistant_response = ""
            if len(session['chat_history']) > 1:  # If there are at least two messages in chat history
                previous_assistant_response = session['chat_history'][-3]['content']  # The last assistant response
            
            # Construct the prompt for the LLM
            prompt = f"""
            Stored Procedure:
            {stored_proc}

            User Request: {text_response}

            Previous Assistant Response: {previous_assistant_response}

            Debug the stored procedure based on the below results and give precise functional details by considering the comments in the code. Avoid technical details.

            {query['data']}
            """
            
            # Use LangChain's LLMChain to process the prompt
            completion = llm.predict(f"You are an expert in debugging stored procedures.\n{prompt}")

            # Add the assistant's response to the session history
            session['chat_history'].append({"role": "assistant", "content": completion.strip()})
            
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
    previous_sql_query = ""
    if len(session['chat_history']) > 1:
        previous_sql_query = session['chat_history'][-2]['content']  # Last assistant response
    print(session['chat_history'])
    # Use the SQL query chain to generate the SQL
    sql_query = sql_query_chain.run({
        "question": user_input,
        "schema_description": schema_description,
        "previous_sql_query": previous_sql_query
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
