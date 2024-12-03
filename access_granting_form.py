import pandas as pd
import os
import requests

# File paths
processed_entries_file = '/Users/dhiveshakilan/Learning/Python/AI/IntelliAISupport/processed_entries.csv'
role_gop_manager_approval = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vS3Ow9LeJpEfTxG2OLVi9LMJUfe961y5tg2ljrFuth_0g3SkeLiSwpIMSU7Blc7HnuL1RxdaHmv0Ekq/pub?output=csv'
gop_approval = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTCBhZST67T28MZH7_D7es_IExPaV9I8M4wJTHiYCDW0cLRm5Iqw3zVMC-7nC273JQmtktnC8LWONy1/pub?output=csv'
# 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTCBhZST67T28MZH7_D7es_IExPaV9I8M4wJTHiYCDW0cLRm5Iqw3zVMC-7nC273JQmtktnC8LWONy1/pub?output=csv'

# Read CSV data from Google Sheets
role_gop_manager_approval_data = pd.read_csv(role_gop_manager_approval)
gop_approval_data = pd.read_csv(gop_approval)

# Load the processed tickets with deduplication
if os.path.exists(processed_entries_file):
    processed_entries = pd.read_csv(processed_entries_file)
    processed_tickets = processed_entries['Ticket No'].drop_duplicates().tolist()
else:
    processed_tickets = []

# Filter to include only unprocessed rows
df_role_manager = role_gop_manager_approval_data[
    (role_gop_manager_approval_data['Do you approve access to the User Specific Role/GOP?'] == 'Yes, I approve.') &
    (role_gop_manager_approval_data['Description'] == 'role') &
    (~role_gop_manager_approval_data['Ticket No'].isin(processed_tickets))
]
df_gop_manager = role_gop_manager_approval_data[
    (role_gop_manager_approval_data['Do you approve access to the User Specific Role/GOP?'] == 'Yes, I approve.') &
    (role_gop_manager_approval_data['Description'].str.contains('gop', case=False, na=False)) &
    (~role_gop_manager_approval_data['Ticket No'].isin(processed_tickets))
]
df_gop = gop_approval_data[
    (gop_approval_data['Do you approve to add this gop in mentioned profile?'] == 'Yes, I approve.') &
    (~gop_approval_data['Ticket No'].isin(processed_tickets))
]
# print(df_gop)
# print(df_gop_manager)
# Process entries and keep track of newly processed tickets
newly_processed_tickets = []

api_url = 'http://127.0.0.1:8080'


# Grant access for roles
for _, row in df_role_manager.iterrows():

    url = api_url+'/storerole'
    data = {
        'user_id': row['User Name'],
        'role': row['Role/Gop Name'],
        'description': row['Description']
    }
    print(data)
    try:
        response = requests.post(url, json=data)
        print(response)
        if response.status_code == 200:
            print(f"Request information stored successfully.")
            print('Access is granted for role manager:', row['Ticket No'])
        else:
            print(f"Failed to store request information: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error storing request information: {e}")
    
    newly_processed_tickets.append(row['Ticket No'])

# Merge and process GOP approvals
matched_df = pd.merge(df_gop_manager, df_gop, on='Ticket No', how='inner')
print(matched_df)
for _, row in matched_df.iterrows():
    print(row['Do you approve to add this gop in mentioned profile?'],row['Do you approve access to the User Specific Role/GOP?'])
    data = {
        'user_id': row['User Name_x'],
        'profile': row['Profile'],
        'gop_name': row['GOP Name'],
        'perimeter': row['Description'],
        'read': '1',
        'write': '1'
        }
    print(data)
    if row['Do you approve to add this gop in mentioned profile?'] == row['Do you approve access to the User Specific Role/GOP?']:
        url = api_url+'/storegop'
        data = {
        'user_id': row['User Name_x'],
        'profile': row['Profile'],
        'gop_name': row['GOP Name'],
        'perimeter': row['Description'],
        'read': '1',
        'write': '1'
        }
        print(data)
        try:
            response = requests.post(url, json=data)
            print(response)
            if response.status_code == 200:
                print(f"Request information stored successfully.")
                print('Access is granted for GOP:', row['Ticket No'])
            else:
                print(f"Failed to store request information: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error storing request information: {e}")
        
        newly_processed_tickets.append(row['Ticket No'])

# Deduplicate newly processed tickets
newly_processed_tickets = list(set(newly_processed_tickets))

# Update processed_entries.csv with new Ticket Nos
if newly_processed_tickets:
    # Create a DataFrame for the new entries
    new_entries_df = pd.DataFrame(newly_processed_tickets, columns=['Ticket No'])
    
    # Append without duplicating headers and prevent duplicate entries
    if os.path.exists(processed_entries_file):
        existing_df = pd.read_csv(processed_entries_file)
        updated_df = pd.concat([existing_df, new_entries_df]).drop_duplicates()
        updated_df.to_csv(processed_entries_file, index=False)
    else:
        new_entries_df.to_csv(processed_entries_file, index=False, header=True)

