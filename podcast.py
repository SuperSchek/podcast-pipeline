#### DATA LEGEND
# 1. podcast_filename
# 2. podcast_title
# 3. keyword
# 4. description
# 5. podcast_s3_url

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

s3 = boto3.client(
    's3',
    aws_access_key_id=secrets.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=secrets.AWS_SECRET_ACCESS_KEY
)

podcasts_global = {}
podcasts_drive=[]
podcasts_converted=[]

def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    check_watchfolder(service)

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
            name = (file.get('name')).replace(" ", "_")
            podcasts_drive.append(name)
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            print ("Welcome to the Python Podcast Pipeline! I found the following files in your watchfolder on Google Drive:")
            print ('\n'.join(map(str, podcasts_drive)))
            print ('******************************')
            confirmation(service, response, (file.get('name')))
            break;

def confirmation(service, response, filename):
    input_continue = raw_input("Proceed? (y/n): ")
    if input_continue is 'y':
        print ('\n')
        feed_info(filename)
        download_files(service, response)
    elif input_continue is 'n':
        print('Okay, doing nothing!')
    else:
        print('Please enter y for yes or n for no:')
        confirmation(service, response, filename)

def feed_info(filename):
    for podcast in podcasts_drive:
        file_name, file_extension = os.path.splitext(filename)
        podcasts_global.update({podcast: []})
        # Get all the info for the title of the podcast
        print ("Please give me all info for %s" % (podcast))
        podcast_type = raw_input("Type of episode (e.g. Review, Discussie): ")
        podcast_title = raw_input("Title of episode (e.g. Atomic Blonde, Game of Thrones Seizoen 7): ")

        podcast_filename = (podcast_type + "_" + podcast_title).replace(" ", "")
        podcasts_global[podcast].append(podcast_filename)

        podcast_title = podcast_type + " | " + podcast_title
        podcasts_global[podcast].append(podcast_title)

        ## Get all the info for the episode description
        podcast_description = raw_input("Episode description: ")

        ## Check of the description contains a key which we can then use to set a hyperlink to out file for S3
        check_for_keywords(podcast, podcast_description)

        print ('\n')

def check_for_keywords(podcast, description):
    if "bespreken" in description:
        podcasts_global[podcast].append('bespreken')
    elif "aflevering" in description:
        podcasts_global[podcast].append('aflevering')
    else:
        keyword = raw_input("No keywords were found in this description. Please enter the you would like to use for the hyperlink to the audiofile on Amazon S3: ")
        podcasts_global[podcast].append(keyword)
    podcasts_global[podcast].append(description)

def download_files(service, response):
    for file in response.get('files', []):
        print('Downloading', file.get('name'), 'from Google Drive. This can take a while...')
        file_id = file.get('id')
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(file.get('name'), 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print ("Download %d%%." % int(status.progress() * 100))
        new_name = (file.get('name')).replace(" ", "_")
        os.rename((file.get('name')), new_name)
    for podcast in podcasts_drive:
        check_extension(podcast)

def check_extension(filename):
    file_name, file_extension = os.path.splitext(filename)
    if file_extension == ".mp3":
        convert_file(filename, "mp3")
    elif file_extension == ".m4a":
        convert_file(filename, "m4a")
    else:
        print("%s does not seem to be an .mp3 or .m4a file and will be ignored. Sorry!" % (filename))

def convert_file(filename, extension):
    converted_filename = podcasts_global[filename][0]
    print ("Converting %s to %s.mp3 in 128kbps. Just a moment..." % (filename, converted_filename))
    podcast = AudioSegment.from_file(filename, extension)
    converted_podcast = (converted_filename + ".mp3")
    podcast.export(converted_podcast, format="mp3", bitrate="128k")
    podcasts_converted.append(converted_podcast)
    os.remove(filename)
    upload_to_s3(converted_podcast)
    os.remove(converted_podcast)

def upload_to_s3(file_to_upload):
    print("Uploading " + file_to_upload + " to the " + secrets.AWS_S3_BUCKET + " bucket on Amazon S3!")
    with open(file_to_upload, 'rb') as data:
        s3.upload_fileobj(data, secrets.AWS_S3_BUCKET, 'wp-content/2017/ %s' % ("001_TEST_" + file_to_upload), ExtraArgs={'ACL': 'public-read'})
    print(file_to_upload + " was uploaded to " + secrets.AWS_S3_BUCKET + " on S3!\n")

    # print('Converting %s which is a %s file.' % (filename, file_extension))

main()
