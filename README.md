# Python Podcast Pipeline
A script to automate the process of uploading my bi-weekly podcast. Feel free to modify it to your own needs.

## What it does:
1. Check and download files from a specified folder on Google Drive using the Drive REST API.
2. Convert the files to .mp3 128kbps using ffmpeg.
3. Upload the converted file to Amazon S3 and set it to public using boto3.
4. Check the current date and set the publication date to be the first upcoming day in our release schedule (in this case: wednesdays and saturdays).
5. Publish a wordpress post including the S3 URL and using the right information. This post is then picked up by feedburner and the podcast is published to iTunes.
