import imaplib
import email
import os
import logging
import subprocess
import json
from langchain.chat_models import ChatOpenAI
from flask import request,jsonify
import requests
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

with open('/Users/dhiveshakilan/Learning/Python/AI/IntelliAISupport/key.json') as f:
    key=json.load(f)

os.environ["OPENAI_API_KEY"] = key['API_KEY']
OWNER = key['OWNER']
REPO = key['REPO']
GITHUB_TOKEN = key['GITHUB_TOKEN']

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/Users/dhiveshakilan/Learning/Python/AI/IntelliAISupport/Log/filesystem_email_trigger.log"),
        logging.StreamHandler()
    ]
)

def authenticate_email():
    """
    Authenticate to Gmail and return an IMAP connection.
    Uses environment variables for email and app password.
    """
    try:
        email_address = os.environ['EMAIL_ADDRESS']
        app_password = os.environ['APP_PASSWORD']
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(email_address, app_password)
        logging.info("Authenticated successfully with Gmail.")
        return mail
    except Exception as e:
        logging.error(f"Failed to authenticate: {e}")
        raise

def send_reply_email(original_email, analysis_result):
    """
    Send a reply to the original email with the analysis result.
    """
    try:
        # Extract the sender and subject from the original email
        sender = original_email['From']
        subject = original_email['Subject']

        # Craft the reply email content
        reply_subject = f"Re: {subject}"
        reply_body = f"Dear User,\n\nHere is the analysis result for your issue:\n\n{analysis_result}\n\nBest regards,\nYour Support Team"
        
        # Create the MIMEText message
        msg = MIMEMultipart()
        msg['From'] = os.environ['EMAIL_ADDRESS']
        msg['To'] = sender
        msg['Subject'] = reply_subject
        
        # Attach the body of the email
        msg.attach(MIMEText(reply_body, 'plain'))
        
        # Send the email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(os.environ['EMAIL_ADDRESS'], os.environ['APP_PASSWORD'])
            server.sendmail(msg['From'], msg['To'], msg.as_string())
        
        logging.info("Reply sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send reply: {e}")

def check_alert(subject_keyword):
    """
    Check for specific alert emails and trigger the cron job if found.
    """
    try:
        mail = authenticate_email()
        email_ids = fetch_emails(mail, subject_keyword)

        if not email_ids:
            logging.info(f"No new '{subject_keyword}' emails found.")
            return False

        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            if status != 'OK':
                logging.error(f"Failed to fetch email with ID {email_id}.")
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            subject = msg.get("Subject")
            logging.info(f"Processing email with subject: {subject}")

            # Extract the body of the email if the subject contains "FILESYSTEM"
            if "filesystem" in subject.lower():
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))

                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()
                # Mark email as read
                mail.store(email_id, '+FLAGS', '\\Seen')
                # Trigger cron job specifically for filesystem alert
                trigger_cron()
                return body

            # If the email is about Autosys Job Failed, process accordingly
            if "autosys job failed" in subject.lower():
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))

                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            body = part.get_payload(decode=True).decode()
                            analysis = debug_user_query(body)
                            logging.info(f"Email Body: {body}")
                            logging.info(f"Analysis: {analysis}")
                            break
                else:
                    body = msg.get_payload(decode=True).decode()
                    analysis = debug_user_query(body)
                    logging.info(f"Email Body: {body}")
                    logging.info(f"Analysis: {analysis}")

                # Mark email as read
                mail.store(email_id, '+FLAGS', '\\Seen')

                # Send the reply email with the analysis result
                send_reply_email(msg, analysis)
                return body

    except Exception as e:
        logging.error(f"Error in check_alert: {e}")
    finally:
        try:
            mail.logout()
            logging.info("Logged out from Gmail.")
        except:
            pass

    return False



def fetch_emails(mail, subject_keyword):
    """
    Fetch unseen emails with the given subject keyword.
    """
    try:
        mail.select('inbox')
        status, data = mail.search(None, f'(UNSEEN SUBJECT "{subject_keyword}")')
        if status != 'OK':
            logging.error("Failed to search emails.")
            return []
        email_ids = data[0].split()
        logging.info(f"Found {len(email_ids)} new emails with the subject '{subject_keyword}'.")
        return email_ids
    except Exception as e:
        logging.error(f"Error fetching emails: {e}")
        return []

def trigger_cron():
    """
    Trigger a cron job or execute a specific task.
    """
    try:
        cron_command = "/Users/dhiveshakilan/Learning/Python/AI/IntelliAISupport/script.sh"  # Replace with your script/command
        subprocess.run(cron_command, shell=True, check=True)
        logging.info(f"Cron job triggered successfully: {cron_command}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to trigger cron job: {e}")
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

def debug_user_query(text_response):
    deal_prompt = f'Give me only the deal id from this response (only number) - {text_response}'
    sql_file_response = f'Give me the stored procedure name (like ole, goat, etc..) from user response (only name) - {text_response}'
    sql_file = llm.predict(sql_file_response)
    print(sql_file)
    stored_proc = github(sql_file)
    print(stored_proc)
    if stored_proc in 'No file found' or stored_proc in 'Failed to connect to the repository.' or stored_proc in 'Failed to fetch the content':
        return stored_proc
    else:
        # Assuming you're using LangChain's LLM, update to the new invoke method
        deal_id = llm.predict(deal_prompt)
        print(deal_id)
        
        api_url = 'http://127.0.0.1:8080/goat'
        response = requests.get(api_url, params={'deal_id': deal_id})
        
        if response.status_code == 200:
            query = response.json()
        
        print(query['data'])
        
        # Construct the prompt for the LLM
        prompt = f"""
    Stored Procedure:
    {stored_proc}

    User Request: {text_response}

    Debug the stored procedure based on the below results and give precise functional details by considering the comments in the code. Avoid technical details.

    {query['data']}
    """
        
        # Use LangChain's LLMChain to process the prompt
        completion = llm.predict(f"You are an expert in debugging stored procedures.\n{prompt}")
        return completion.strip()

if __name__ == "__main__":
    with open('/Users/dhiveshakilan/Learning/Python/AI/IntelliAISupport/key.json') as f:
        key=json.load(f)

    os.environ['EMAIL_ADDRESS'] = key['EMAIL_ADDRESS']
    os.environ['APP_PASSWORD'] = key['APP_PASSWORD']
    # Environment variable setup

    subject_keywords = ["FILESYSTEM", "AUTOSYS Job Failed"]  # Keywords to search in email subject
    logging.info("Starting 'FILESYSTEM' email check...")
    if check_alert(subject_keywords[0]):
        logging.info("'FILESYSTEM' email processed and cron triggered.")
    else:
        logging.info("No 'FILESYSTEM' email found or processed.")

    logging.info("Starting 'AUTOSYS Job Failed' email check...")
    if check_alert(subject_keywords[1]):
        logging.info("'AUTOSYS Job Failed' email processed and analyzing the log.")
        logging.info("'AUTOSYS Job Failed' email processed and analysis is sent to mail.")
    else:
        logging.info("No 'AUTOSYS Job Failed' email found or processed.")
