## flickrgroup.py

This script creates a local folder named after the Flickr Group ID and downloads the highest resolution pics available into it. 

An accompanying CSV file (list.csv) is created and save in the same folder. 

The CSV file contains the following metadata for each photo:
PICID - The Flickr photo id  
PICURL - URL of the high-res photo  
TAKEN - The date the photo was taken  
REALNAME - Photographers name  
TITLE - Title provided to Flickr  
DESCRIPTION - Flickr Description field  
PATH_ALIAS - User-provided field, maybe useful to spot user-correlated groups.  


## Usage:

python flickrgroup.py

You'll be prompted to enter the URL of the Flickr Group you would like to scrape. Paste in the URL.

Once this entered the Photo ID's will be downloaded first, then processed to retrieve pics/data.

All output is save in the folder named after the Group ID.

Each image takes about 1-2 seconds to download including JPG and data fields (CSV).

## Dependencies

flickrapi  
wgetter  

## API Reference

https://www.flickr.com/services/api/

## TODO

Create folder under group name instead of ID.  
Automated elimination of non-face images.  
Check for existing files before download and resume.  
Integration with additional data sources.  
