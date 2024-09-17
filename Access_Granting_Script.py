import imaplib
import email
from email.header import decode_header
import requests
import google.generativeai as genai
import re

# Configure API key
genai.configure(api_key='AIzaSyAMF0mumr0TVRolQlu-62UrJEQrV_N8EaI')  # Replace with your API key

# Email credentials and configuration
email_address = 'dhivesh18122000@gmail.com'
app_password = 'stwf byvp tuhv lskz'
imap_server = 'imap.gmail.com'
subject_keyword = "Approval Request for "

# API URL for fetching and marking requests
api_url = 'http://192.168.84.208:8080'  # Replace with your API endpoint

# Function to generate Gemini API responses
def get_gemini_response(prompt):
    model = genai.GenerativeModel("gemini-1.0-pro-latest")  # Replace with desired model
    response = model.generate_content(prompt)
    return response.text

# Function to get request details from the API
def get_requests_from_api():
    response = requests.get(f'{api_url}/get-request')
    if response.status_code == 200:
        # Filter only the requests with status 'In progress'
        in_progress_requests = [req for req in response.json() if req.get('status') == 'In progress']
        return in_progress_requests
    else:
        print(f"Failed to fetch requests: {response.status_code}")
        return []
    

# Function to analyze email content using AI
def analyze_email_content(content):
    prompt = f"Analyze this email content and determine if it implies approval: {content}"
    response = get_gemini_response(prompt)
    return 'approve' in response.lower() or 'approved' in response.lower()

# Function to process emails from the email IDs
def process_email_from_ids(mail, email_ids, request_id, role_or_gop):
    for email_id in email_ids:
        try:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            if status == 'OK':
                msg = email.message_from_bytes(msg_data[0][1])
                processed = process_email(msg, request_id, role_or_gop)
                if processed:
                    mail.store(email_id, '+FLAGS', '\\Seen')  # Mark as read
                    # Re-select the inbox to synchronize status
                    mail.select('inbox')
                    return True
            else:
                print(f"Failed to fetch email: {status}")
        except Exception as e:
            print(f"Error processing email ID {email_id}: {e}")
    return False

# Function to process the email and grant access if approved
def process_email(msg, request_id, role_or_gop):
    """Process the email and grant access if approved."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" or part.get_content_type() == "text/html":
                try:
                    body = part.get_payload(decode=True).decode()
                except:
                    body = ""
                if analyze_email_content(body):
                    print(f"Approval found in email for request ID: {request_id}.")
                    grant_access_from_email(request_id, role_or_gop)
                    return True
    else:
        try:
            body = msg.get_payload(decode=True).decode()
        except:
            body = ""
        if analyze_email_content(body):
            print(f"Approval found in email for request ID: {request_id}.")
            grant_access_from_email(request_id, role_or_gop)
            return True
    return False

# Function to grant access based on email content
def grant_access_from_email(request_id, role_or_gop):
    # Grant access based on the request detail (GOP or role)
    print(f"Granting access for: {role_or_gop}.")

    # Implement your database access logic here

    # Mark request as processed
    mark_request_as_processed(request_id)

# Function to mark request as processed
def mark_request_as_processed(request_id):
    mark_api_url = f'{api_url}/mark-request'
    data = {
        'request_id': request_id,
        'status': 'processed'  # Update status to 'processed'
    }
    response = requests.post(mark_api_url, json=data)
    if response.status_code == 200:
        print(f"Request marked as processed.")
    else:
        print(f"Failed to mark request as processed: {response.status_code}")

if __name__ == "__main__":    
    requests_from_api = get_requests_from_api()
    print(requests_from_api)
    if requests_from_api:
        # Set up the mail connection
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, app_password)
        mail.select('inbox')

        for request in requests_from_api:
            request_id = request.get('request_id')
            role_or_gop = request.get('role_or_gop')
            manager_email = request.get('manager_email')
            subject = f'{subject_keyword}{role_or_gop} - Reference ID: {request_id}'
            print(subject)
            # Search for relevant emails
            status, data = mail.search(None, f'(UNSEEN FROM "{manager_email}" SUBJECT "{subject}")')
            email_ids = data[0].split()
            print(status, data)
            if email_ids:
                # Process the emails found
                approval_found = process_email_from_ids(mail, email_ids, request_id, role_or_gop)
                if approval_found:
                    print(f"Approval granted and access provided for request ID {request_id}.")
                else:
                    print(f"No approval found in emails for request ID {request_id}.")
            else:
                print(f"No relevant emails found for request ID {request_id}.")
        
        # Logout after processing
        mail.logout()
    else:
        print("No requests found to process.")
