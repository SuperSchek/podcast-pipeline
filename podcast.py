## Drive REST API imports
from __future__ import print_function
import httplib2
import os
import io
from apiclient import errors
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None
# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Filmerds Podcast Pipeline'

## Boto3 imports (for S3 upload)
import boto3

## PyDub imports (for audio conversion)
from pydub import AudioSegment

## File imports
import secrets

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


def download(service):
    results = service.files().list(
        pageSize=3,fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Found podcasts, starting download.')
        for item in items:
            print('Downloading', item.get('name'))
            file_id = item.get('id')
            request = service.files().get_media(fileId=file_id)
            fh = io.FileIO(item.get('name'), 'wb')

def check_watchfolder(service):
    page_token = None
    while True:
        response = service.files().list(q=("'%s' in parents and trashed = false" % secrets.DRIVE_WATCHFOLDER_ID),
                                        spaces='drive',
                                        fields='nextPageToken, files(id, name)',
                                        pageToken=page_token).execute()
        for file in response.get('files', []):
            # Process change
            print ('Found file: %s (%s)' % (file.get('name'), file.get('id')))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break;

main()

s3 = boto3.client(
    's3',
    aws_access_key_id=secrets.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=secrets.AWS_SECRET_ACCESS_KEY
)

# with open('pic.png', 'rb') as data:
#     s3.upload_fileobj(data, 'filmerds-podcast-wp', 'wp-content/picture.png', ExtraArgs={'ACL': 'public-read'})


# podcast = AudioSegment.from_file("podcast.mp3", "mp3")
# podcast.export("podcast_converted.mp3", format="mp3", bitrate="128k")
