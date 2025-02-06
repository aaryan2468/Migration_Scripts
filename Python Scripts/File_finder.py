from google.oauth2 import service_account
from googleapiclient.discovery import build
import re
import csv
import os
from urllib.parse import urlparse, parse_qs


SERVICE_ACCOUNT_FILE = 'Service_Key.json'

# Scopes for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive']

credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES,
            subject='ccarlson@infoblox.com'
)

drive_service_new = build('drive', 'v3', credentials=credentials)
'''
f = drive_service_new.files().get(fileId='11_YKf15SrbYaOW3dzdna6mDspRIaHQSO').execute()

currentOwner = f['owners'][0]['emailAddress']

print(currentOwner)
'''
'''file = drive_service_new.files().get(fileId='1_Z2DySqLl9W8cajYggat5mUq6K6IrpNoV_1FAomxGI4', fields='id, name, parents, driveId').execute()

parent_id = file.get('parents', [])[0] if 'parents' in file else None

print(parent_id)'''

#output=[(perm['id'], perm.get('emailAddress', ''), perm['role']) for perm in permissions]
#print(output)
def get_file_path(file_id,drive_service,drive_service_v2):
    parent_owner=''
    try:
        file = drive_service.files().get(fileId=file_id, fields='id, name, parents, driveId, mimeType').execute()
        file_name= file['name']
        file_path = file['name']
        mimetype = file['mimeType']
        #size=file['size']
        parent_id = file.get('parents', [])[0] if 'parents' in file else None
        #if parent_id: 
        while parent_id:
            f = drive_service_v2.files().get(fileId=parent_id).execute()
            parent_owner = f['owners'][0]['emailAddress']
            parent = drive_service.files().get(fileId=parent_id, fields='id, name, parents').execute()
            driveId = parent['id']
            file_path = parent['name'] + '/' + file_path
            parent_id = parent.get('parents', [])[0] if 'parents' in parent else None
            
        return file_path,file_name,parent_owner, mimetype
    except:
        return 'not found','not found','not found','not found'

with open('input.csv', mode='r+', newline='', encoding="utf8") as file:
    reader = csv.reader(file)
    rows = list(reader)
    first_row= 1
    for row in rows:
        credentials1 = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES,
            subject=row[0]
        )

        # Build the Drive API service
        drive_service1 = build('drive', 'v3', credentials=credentials1)
        drive_service_v2 = build('drive', 'v2', credentials=credentials1)

        if first_row==1:
            row.extend(['File Path', 'File Name','Drive Owner','mimetype'])
            first_row=0
        else:           
            file_url = row[1]
            file_location = get_file_path(file_url, drive_service1, drive_service_v2)
            print(file_location)
            row.extend(file_location)
            
                
    file.seek(0)
    file.truncate(0)
    writer = csv.writer(file)
    writer.writerows(rows)
