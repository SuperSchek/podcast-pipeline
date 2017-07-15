## Drive REST API imports
from __future__ import print_function
import httplib2
import os
import io
from apiclient import errors
from apiclient import discovery
from googleapiclient.http import MediaIoBaseDownload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

## File imports
import secrets

## Boto3 imports (for S3 upload)
import boto3

## PyDub imports (for audio conversion)
from pydub import AudioSegment

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = secrets.APPLICATION_NAME

podcasts_drive=[]


def get_credentials():
    """
    Gets valid user credentials from storage.
    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'drive-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def check_watchfolder(service):
    page_token = None
    while True:
        response = service.files().list(q=("'%s' in parents and trashed = false" % secrets.DRIVE_WATCHFOLDER_ID),
                                        spaces='drive',
                                        fields='nextPageToken, files(id, name)',
                                        pageToken=page_token).execute()
        for file in response.get('files', []):
            ## Get list of files available for donwload
            podcasts_drive.append((file.get('name')))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            print ("I found the following files:")
            print ('******************************')
            print ('\n'.join(map(str, podcasts_drive)))
            print ('******************************')
            input_continue = raw_input("Proceed? (y/n): ")
            if input_continue is 'y':
                print('On it!')
            elif input_continue is 'n':
                print('Okay, doing nothing!')
                break;
            else:
                print('Please enter y for yes or n for no:')
            break;
    for podcast in podcasts_drive:
        print ("Running check_extensions for %s" % podcast)
        check_extension(podcast)

def check_extension(filename):
    file_name, file_extension = os.path.splitext(filename)
    if file_extension == ".mp3":
        # convert_file(filename, ".mp3")
        print ("Checked extension for %s and found %s" % (file_name, file_extension))
    elif file_extension == ".m4a":
        print ("Checked extension for %s and found %s" % (file_name, file_extension))
        # convert_file(filename, ".m4a")
    else:
        print("%s does not seem to be an .mp3 or .m4a file. Sorry!")

def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    check_watchfolder(service)

main()
