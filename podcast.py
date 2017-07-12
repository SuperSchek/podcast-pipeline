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

def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    check_watchfolder(service)


def download(service, response):
    for file in response.get('files', []):
        print('Downloading', file.get('name'))
        file_id = file.get('id')
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(file.get('name'), 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print ("Download %d%%." % int(status.progress() * 100))
        convert_files(file.get('name'))

def check_watchfolder(service):
    page_token = None
    while True:
        response = service.files().list(q=("'%s' in parents and trashed = false" % secrets.DRIVE_WATCHFOLDER_ID),
                                        spaces='drive',
                                        fields='nextPageToken, files(id, name)',
                                        pageToken=page_token).execute()
        for file in response.get('files', []):
            # Process change
            print ('Found file: %s' % (file.get('name')))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            input_continue = raw_input("Download, convert and publish these files? (y/n): ")
            if input_continue is 'y':
                print('On it!')
                download(service, response)
            elif input_continue is 'n':
                print('Okay, doing nothing!')
                break;
            else:
                print('Please enter y for yes or n for no:')
            break;

def convert_files(filename):
    file_name, file_extension = os.path.splitext(filename)
    if file_extension == ".mp3":
        podcast = AudioSegment.from_file(filename, "mp3")
        input_mp3convert = raw_input("Geef de titel van deze file: " + filename)
        if input_mp3convert:
            podcast.export((input_mp3convert + ".mp3"), format="mp3", bitrate="128k")


    # print('Converting %s which is a %s file.' % (filename, file_extension))

main()

s3 = boto3.client(
    's3',
    aws_access_key_id=secrets.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=secrets.AWS_SECRET_ACCESS_KEY
)

# with open('pic.png', 'rb') as data:
#     s3.upload_fileobj(data, 'filmerds-podcast-wp', 'wp-content/picture.png', ExtraArgs={'ACL': 'public-read'})
