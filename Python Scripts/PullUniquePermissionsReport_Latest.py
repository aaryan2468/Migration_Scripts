import concurrent.futures
import csv
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import os
import numpy as np

# Path to the service account key JSON file. This should be replaced if required.
SERVICE_ACCOUNT_FILE = 'Service_Key.json'

# Scopes for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive']

#Function to fetch all permissions for a file or folder.
def get_all_permissions(file_id, drive_service):
    permissions = drive_service.permissions().list(fileId=file_id, fields="permissions(id, emailAddress, role)").execute().get('permissions', [])
    return [(perm['id'], perm.get('emailAddress', ''), perm['role']) for perm in permissions]

#Function to fetch emails of removed user permissions.
def get_all_permissions_child(file_id, parentPermissions, drive_service):
    permissions = drive_service.permissions().list(fileId=file_id, fields="permissions(id, emailAddress, role)").execute().get('permissions', [])
    removed_emails = ''
    flag=0
    child_permission_emails = ';'.join([perm.get('emailAddress', '') for perm in permissions])
    for parent in parentPermissions:
        if parent[1] in child_permission_emails:
            flag += 1
        else:
            if removed_emails == '':
                removed_emails = parent[1]
            else:
                removed_emails = removed_emails + ';' + parent[1]
    return removed_emails

# Function to check if file/folder has different permissions from its parent
def has_different_permissions(file_id, parent_permissions, drive_service):
    file_permissions = get_all_permissions_child(file_id, parent_permissions, drive_service)
    return file_permissions

# Function to get file path
def get_file_path(file_id,drive_service):
    file = drive_service.files().get(fileId=file_id, fields='id, name, parents, driveId').execute()
    driveId = file_id
    file_path = file['name']
    parent_id = file.get('parents', [])[0] if 'parents' in file else None
    while parent_id:
        parent = drive_service.files().get(fileId=parent_id, fields='id, name, parents').execute()
        driveId = parent['id']
        file_path = parent['name'] + '/' + file_path
        parent_id = parent.get('parents', [])[0] if 'parents' in parent else None
    return file_path, driveId

# Fetch all files and folders from Google Drive
def fetch_all_files_for_user(user_email, drive_service):
    files = []
    page_token = None

    while True:
        response = drive_service.files().list(
            q=f"trashed=false and '{user_email}' in owners",
            fields="nextPageToken, files(id, name, mimeType, parents)",
            pageToken=page_token
        ).execute()

        files.extend(response.get('files', []))

        page_token = response.get('nextPageToken')
        if not page_token:
            break  # No more pages, exit loop
    return files

# Function to store the list of completed users in a CSV File
def completed_logs(user_email,exception_flag):
    completion_status = ''
    if exception_flag == 1:
        completion_status = 'Completed with errors'
    else:
        completion_status = 'Completed'
    dt = str(datetime.datetime.now())
    file_exists = os.path.isfile('completed_log.csv') and os.path.getsize('completed_log.csv') > 0
    with open('completed_log.csv', 'a', newline='') as csvfile:
        fieldnames = ['User Email','Completion Status','Timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({'User Email': user_email, 'Completion Status': completion_status, 'Timestamp': dt})

# Function to handle the error and store the message in a CSV file
def handle_error(user_email,file_id,error_message):
    file_exists = os.path.isfile('error_log.csv') and os.path.getsize('error_log.csv') > 0
    with open('error_log.csv', 'a', newline='') as csvfile:
        fieldnames = ['File ID','Error Message','Email']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({'File ID':file_id, 'Error Message': error_message,'Email' : user_email})
    

# Fetch files with different permissions from their parent folders
def fetch_files_with_different_permissions(user_email):
    output_data = []
    exception_flag = 0
    try:
        print(user_email)
        error_data = []
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES,
            subject=user_email
        )
        drive_service = build('drive', 'v3', credentials=credentials)
        files = fetch_all_files_for_user(user_email, drive_service)
        for file_info in files:
            try:
                parent_id = file_info.get('parents', [])[0] if 'parents' in file_info else None
                if parent_id:
                    parent_permissions = get_all_permissions(parent_id, drive_service)
                    parent_email = ';'.join([parent[1] for parent in parent_permissions])
                    permissions = has_different_permissions(file_info['id'], parent_permissions, drive_service)
                    if len(permissions) > 0:
                        driveowner = user_email
                        file_path, driveId = get_file_path(file_info['id'], drive_service)
                        if len(driveId) > 0:
                            permissions1 = drive_service.permissions().list(fileId=driveId, supportsAllDrives=True, fields="permissions(id,emailAddress,displayName,role)").execute()
                            owners = [permission for permission in permissions1['permissions'] if permission['role'] == 'owner']
                            driveowner = owners[0]['emailAddress']
                        output_data.append({
                            'Name': file_info['name'],
                            'ID': file_info['id'],
                            'Type': file_info['mimeType'],
                            'Path': file_path,
                            'Owner_Email': user_email,
                            'Removed_Users': permissions,
                            'Parent_Permission_Users': parent_email,
                            'Drive Owner': driveowner
                        })
            except Exception as e:
                        error_message = str(e)
                        if 'insufficientFilePermissions' in error_message:
                            print("Error: The user does not have sufficient permissions for this file.")
                            # Extract the file ID from the error message (assuming the error message format is consistent)
                            file_id = file_info['id'] #error_message.split('files/')[1].split('/')[0]
                            # Handle the error appropriately, for example, skip this iteration
                            #handle_error(file_id, error_message, user_email)
                            handle_error(user_email,file_id,error_message)
                            exception_flag = 1
                        else:
                            print("An unexpected error occurred:", error_message)
    except Exception as e:
        error_message = str(e)
        if 'internalError' in error_message:
            print("Internal error")
            exception_flag = 1
        else:
            print("An unexpected error occurred:", error_message)
                
    completed_logs(user_email,exception_flag)
    if len(output_data)==0:
        output_data.append({
                            'Name': np.nan,
                            'ID': '',
                            'Type': '',
                            'Path': '',
                            'Owner_Email': '',
                            'Removed_Users': '',
                            'Parent_Permission_Users': '',
                            'Drive Owner': ''
                        })
    df = pd.DataFrame(output_data)
    df.to_csv('files_with_removed_permissions-'+user_email+'.csv', index=False)
    return output_data

# Store output in CSV using pandas
def store_output_to_csv(output_data):
    df = pd.DataFrame(output_data)
    df.to_csv('files_with_removed_permissions.csv', index=False)

# Fetch files with different permissions from each user in parallel
def fetch_files_parallel(users):
    output_data = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit tasks for each user
        futures = [executor.submit(fetch_files_with_different_permissions, user) for user in users]
        # Retrieve results as they become available
        for future in concurrent.futures.as_completed(futures):
            output_data.extend(future.result())
        
    return output_data

def main():
    # Read user emails from CSV
    open("completed_log.csv", "w").close()
    open("error_log.csv", "w").close()
    with open('User_Emails.csv', mode='r', newline='') as file:
        reader = csv.reader(file)
        counter = 0
        users = []
        files=[]
        for row in reader:
            files.append('files_with_removed_permissions-'+row[0]+'.csv')
            users.append(row[0])
            if counter == 9:
                output_data=fetch_files_parallel(users)
                users=[]
                counter=0
                print(users)
            counter=counter+1
        #users = [row[0] for row in reader]
    # Fetch files with different permissions from each user in parallel
    output_data = fetch_files_parallel(users)
    # Store output in CSV
    #store_output_to_csv(output_data)
    # merging two csv files

    df = pd.concat(map(pd.read_csv, files), ignore_index=True)
    df.dropna(subset=['Name'], inplace=True)
    df.to_csv('Combined_output.csv', index=False)

if __name__ == "__main__":
    main()
