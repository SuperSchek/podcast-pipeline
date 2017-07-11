import boto3
import secrets

s3 = boto3.client(
    's3',
    aws_access_key_id=secrets.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=secrets.AWS_SECRET_ACCESS_KEY
)

with open('pic.png', 'rb') as data:
    s3.upload_fileobj(data, 'filmerds-podcast-wp', 'wp-content/picture.png', ExtraArgs={'ACL': 'public-read'})
