# Python Podcast Pipeline
A python script to automate the process of uploading my bi-weekly podcast. Feel free to modify it to your own needs. This script was built with Python 2.7.10 and tested on both MacOS and Windows.

## What it does:
1. Check and download files from a specified folder on Google Drive using the Drive REST API.
2. Convert the files to .mp3 128kbps using ffmpeg.
3. Upload the converted file to Amazon S3 and set it to public using boto3.
4. Check the current date and set the publication date to be the first upcoming day in our release schedule (in this case: wednesdays and saturdays).
5. Publish a wordpress post including the S3 URL and using the right information. This post is then picked up by feedburner and the podcast is published to iTunes.

## How to use:
In order to use this script you're going to need a few things first.
### Prerequisites
Working installations of:
- Python 2.7 (No idea if it'll work with Python 3, I'm a bit of Python noob but you're welcome to try.)
- PIP & virtualenv
- <a href="https://github.com/FFmpeg/FFmpeg">FFmpeg</a>
