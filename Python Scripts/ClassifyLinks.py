from google.oauth2 import service_account
from googleapiclient.discovery import build
import re
import csv
import os

# Path to the service account key JSON file. This should be replaced if required.
SERVICE_ACCOUNT_FILE = 'Service_Key.json'

# Scopes for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive']

# Service account credentials for authentication
credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES,
            subject='user@gmail.com'
)

# Build the Drive API service
drive_service = build('drive', 'v3', credentials=credentials)

def get_drive_service(user_email):
    credentials_new = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES,
            subject=user_email
    )

    # Build the Drive API service
    drive_service_new = build('drive', 'v3', credentials=credentials_new)
    return drive_service_new

def handle_error(user_email,file_id,error_message):
    file_exists = os.path.isfile('error_log.csv') and os.path.getsize('error_log.csv') > 0
    with open('error_log.csv', 'a', newline='') as csvfile:
        fieldnames = ['File ID','Error Message','Email']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({'File ID':file_id, 'Error Message': error_message,'Email' : user_email})


def get_all_permissions(file_id, drive_service):
    permissions = drive_service.permissions().list(fileId=file_id, fields="permissions(id, emailAddress, role)",supportsAllDrives=True).execute().get('permissions', [])
    return [(perm['id'], perm.get('emailAddress', ''), perm['role']) for perm in permissions]

def get_file_location(file_url):
    # Extract file ID from the URL
    file_id = ''
    user_email='user@gmail.com'
    for url in file_url:
        if 'folders' in url:
            file_id_match = re.search(r'/folders/(.*?)(?:/|$)', url)
        else:
            file_id_match = re.search(r'/d/(.*?)(?:/|$)', url)
        if file_id_match:
            file_id = file_id_match.group(1)
            print(file_id)
    if len(file_id)==0:
        return ["","",""]

    try:
        # Get file metadata including parents
        file_metadata = drive_service.files().get(fileId=file_id, fields="id, name, parents, ownedByMe, driveId", supportsAllDrives=True).execute()
        if file_metadata.get('ownedByMe'):            
            return ["My Drive", "",""]
        elif file_metadata.get('driveId'):
            try:
                #print(file_metadata.get('driveId'))
                #permissions1 = drive_service.permissions().list(fileId=file_metadata.get('driveId'), supportsAllDrives=True, fields="permissions(id,emailAddress,displayName,role)").execute()
                #owners = [permission for permission in permissions1['permissions'] if permission['role'] == 'organizer']
            #for permission in permissions1['permissions']:
              #  print(permission['role'])

               
                driveowner = ''
                for permission in get_all_permissions(file_metadata.get('driveId'),drive_service):
                    driveowner = driveowner+';'+ permission[1]          
                try:
                    drive_metadata = drive_service.drives().get(driveId=file_metadata.get('driveId'), fields='name').execute()
                    return ["Shared Drive", driveowner, drive_metadata['name']]
                except:
                    print("An error occurred:", e)
                    handle_error(user_email,file_id,e)
                    return ["Shared Drive", driveowner,""]
            except Exception as e:
                try:
                    owners = [permisSheikh Mehboob Akram-SDrive logsion for permission in get_all_permissions(file_id,drive_service) if permission[2] == 'organizer']
                    print(owners)
                    drive_service_new = get_drive_service(owners[0][1])
                    try:
                        drive_metadata = drive_service_new.drives().get(driveId=file_metadata.get('driveId'), fields='name').execute()
                        return ["Shared Drive", owners[0][1],drive_metadata['name']]
                    except:
                        print("An error occurred:", e)
                        handle_error(user_email,file_id,e)
                        return ["Shared Drive", owners[0][1],""]
                except:
                    print("An error occurred:", e)
                    handle_error(user_email,file_id,e)
                    return ["Shared Drive", "",""]
                    
        else:
            try:
                owners = [permission for permission in get_all_permissions(file_id,drive_service) if permission[2] == 'owner']
                print(owners)
                fileowner = owners[0][1]
                return ["Personal Drive", fileowner,""]
            except Exception as e:
                print("An error occurred:", e)
                handle_error(user_email,file_id,e)
                return ["Personal Drive", "",""]

        # If file is found, determine location
       
    except Exception as e:
        print("An error occurred:", e)
        handle_error(user_email,file_id,e)
        return ["","",""]
    
# Example usage
with open('SDrive log.csv', mode='r+', newline='') as file:
    output_data = []
    reader = csv.reader(file)
    rows = list(reader)
    first_row=1
    for row in rows:
        if first_row==1:
            row.extend(['Location','Drive Owner', 'Drive Name'])
            first_row=0
        else:
            if "Link Doesn't found" in row[7]:
                file_url = [row[4],row[5],row[6]]
                file_location = get_file_location(file_url)
                print(file_location)
                row.extend(file_location)
            
                
    file.seek(0)
    file.truncate(0)
    writer = csv.writer(file)
    writer.writerows(rows)
