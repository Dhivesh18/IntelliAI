import imaplib
import email
import os
import logging
import subprocess
import json

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

            # Mark email as read
            mail.store(email_id, '+FLAGS', '\\Seen')

            # Trigger cron job
            trigger_cron()
            return True

    except Exception as e:
        logging.error(f"Error in check_alert: {e}")
    finally:
        try:
            mail.logout()
            logging.info("Logged out from Gmail.")
        except:
            pass
    return False

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
        logging.info("'AUTOSYS Job Failed' email processed and cron triggered.")
    else:
        logging.info("No 'AUTOSYS Job Failed' email found or processed.")
