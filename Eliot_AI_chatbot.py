import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
import requests
import uuid
import re

# Configure API key directly (not recommended for production)
genai.configure(api_key='AIzaSyAMF0mumr0TVRolQlu-62UrJEQrV_N8EaI')  # Replace with your actual API key

# Define roles and their descriptions
roles = {
    "admin": "Admin has full access to all features and settings.",
    "moderator": "Moderator can manage user content and oversee interactions.",
    "user": "User can access standard features and content.",
    "guest": "Guest has limited access and can view public content only."
    # "COM_FLOW":"Write role fo"
}

# Define a dictionary to map portfolio names to their GOPs
gop_mapping = {
    "PDS_ABC": "DPS",
    "PDS_XYZ": "DPS",
    "PDS_DEF": "DPS",
    "XYZ_ABC": "XYZ",
    "ABC_DEF": "ABC"
    # Add more portfolio-to-GOP mappings here
}
bdr_mapping = {
    "1234": "DPSFGU",
    "78689": "WTYIUI"
}
# Function to check user access to GOP (Placeholder)
def user_has_access_to_gop(gop):
    # Implement logic to check if the user has access to the GOP
    return False  # Simulate lack of access

# Function to get a response from the chatbot based on role or GOP
def validate_entity(entity, entity_type):
    if entity_type == "role":
        return entity in roles
    elif entity_type == "gop":
        return entity in gop_mapping.values()
    return False

# Function to generate Gemini API responses
def get_gemini_response(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.0-pro-latest")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating Gemini response: {e}")
        return "I'm having trouble processing your request right now."

# Function to send an approval email to the manager
def send_approval_email(user_email, manager_email, role_or_gop, request_id):
    sender_email = "dhivesh18122000@gmail.com"  # Replace with your email
    sender_password = 'stwf byvp tuhv lskz'  # Use the app-specific password
    subject = f"Approval Request for {role_or_gop} - Reference ID: {request_id}"
    
    # Updated prompt to generate a more explicit access request email
    prompt = (
        f"Compose a formal email requesting approval for the following role or GOP access:\n"
        f"User {user_email} is requesting access to the role or GOP: {role_or_gop}.\n"
        f"The request ID for this approval is {request_id}.\n"
        f"Please review and provide your approval.\n"
        f"Sincerely, Eliot Team"
    )
    
    body = get_gemini_response(prompt)
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = manager_email

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:  # Use Gmail SMTP server
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("Approval email sent.")

        # Store request information in API
        store_request_info(request_id, user_email, role_or_gop, manager_email)
    except Exception as e:
        print(f"Failed to send email: {e}")

# Function to store request information in an API
def store_request_info(request_id, user_email, role_or_gop, manager_email):
    api_url = 'http://192.168.84.208:8080/store-request'
    data = {
        'request_id': request_id,
        'role_or_gop': role_or_gop,
        'user_email': user_email,
        'manager_email': manager_email,
        'status': 'In progress'
    }
    try:
        response = requests.post(api_url, json=data)
        if response.status_code == 200:
            print(f"Request information stored successfully.")
        else:
            print(f"Failed to store request information: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error storing request information: {e}")

# Function to extract roles from the user input
def extract_roles_from_message(message):
    roles_list = ', '.join(roles.keys())
    prompt = f"From the following list: {roles_list}, which roles are mentioned in the sentence: '{message}'?"
    response = get_gemini_response(prompt).strip()
    return [role for role in roles.keys() if role.lower() in response.lower()]

# Function to extract GOPs from the user input (not predicting the gops correctly)
def extract_gops_from_message(message):
    potential_gops = []
    message_split = re.split(r"[ ,]", message)
    for i in message_split:
        if i in set(gop_mapping.values()):
            potential_gops.append(i)

    return potential_gops
    
# Function to identify the portfolio from the user input
def extract_portfolio_from_message(message):
    portfolio_set = set(name for name in gop_mapping.keys())

    # Split the message into lowercase words for efficient search
    words = re.split(r"[ ,]", message)

    # Iterate over the words and check if they match any portfolio names
    extracted_portfolios = []
    for word in words:
        if word in portfolio_set:
            extracted_portfolios.append(word)

    return extracted_portfolios

def check_yes_no(user_email, gop_role_details, gop_role):
    request_access = input(f"Chatbot: Would you like to request access for this {gop_role} {gop_role_details}? (yes/no) ")
    if request_access.lower() == "yes":
        manager_email = input("Chatbot: Please enter your manager's email for approval: ")
        request_id = generate_request_id()
        send_approval_email(user_email, manager_email, gop_role, request_id)
        return f"Approval request for {gop_role_details}: {gop_role} has been sent to your manager."
    else:
        return "No access request was made."
    
def extract_bdr_from_message(message):
    bdr_list = ', '.join(set(bdr_mapping.keys()))
    prompt = f"From the following list: {bdr_list}, which bdr is mentioned in the sentence: '{message}'?"
    response = get_gemini_response(prompt).strip()
    return [bdr for bdr in bdr_mapping.keys() if bdr in response.lower()]   
    
    
def chat():
    print('Chatbot: Hello! Please enter your email id:')
    user_email = input("You: ")

    while True:
        
        roles_requested = []
        gops_requested = []
        portfolio_requested = []
        responses = []

        print("Chatbot: How can I assist you today?")
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Chatbot: Goodbye!")
            break
        
        roles_requested = extract_roles_from_message(user_input) #roles
        gops_requested = extract_gops_from_message(user_input) #gops
        portfolio_requested = extract_portfolio_from_message(user_input) #portfolio
        bdr_requested = extract_bdr_from_message(user_input)
        # eliot_code = extract_eliot_code_from_message(user_input)

        print(f"Debugging: {roles_requested,gops_requested},{portfolio_requested},{bdr_requested}")
        
        # Handle portfolio requests
        if portfolio_requested:
            for portfolio in portfolio_requested:
                gop = gop_mapping.get(portfolio, None)
                if gop:
                    gops_requested.append(gop)
                else:
                    responses.append("Portfolio not recognized.")
        
        # Handle role requests
        if roles_requested:
            for role in roles_requested:
                if user_has_access_to_gop(role):
                    responses.append(f"You already have access to role: {role}.")
                else:
                    if validate_entity(role, "role"):
                        responses.append(check_yes_no(user_email, "role", role))
                    else:
                        responses.append(f"{role} - Role not found.")
        
        # Handle GOP requests
        if gops_requested is not None:
            for gop in gops_requested:
                if user_has_access_to_gop(gop):
                    responses.append(f"You already have access to GOP: {gop}.")
                else:
                    if validate_entity(gop, "gop"):
                        responses.append(check_yes_no(user_email, "gop", gop))
                    else:
                        responses.append(f"{gop} - Gop not found.")
        if bdr_requested:
            for bdr in bdr_requested:
                if bdr:
                    responses.append("Eliot code is already created in Eliot")
                else:    
                    responses.append("Eliot code not created in Eliot")   

        # Handle if no roles or GOPs are identified
        if not roles_requested and not gops_requested and not portfolio_requested and not bdr_requested:
            responses.append("Reach out to Eliot Support.")
        
        for response in responses:
            print(f"Chatbot: {response}")

        print('Chatbot: Is there anything else you are looking for? (yes/no) ')
        follow_up = input("You: ")
        if follow_up.lower() in ['no', 'quit', 'exit']:
            print("Chatbot: Goodbye!")
            break

def generate_request_id():
    return str(uuid.uuid4())

if __name__ == "__main__":
    chat()
