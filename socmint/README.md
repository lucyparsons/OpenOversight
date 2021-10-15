Social Media
============

Code in `grab_socmint.py` grabs images from public Twitter accounts.

It calls the code from here which uses `tweepy`:
`https://github.com/miguelmalvarez/downloadTwitterPictures/blob/master/src/run.py`

To run:
 - Clone the downloadTwitterPictures project. Install any new dependencies (will run using python3- use pip3 to install)
 - In the root directory of this project, copy the `sample-config.cfg` file and rename it to be `config.cfg`
 - Go to `https://apps.twitter.com/` and create a Twitter app
 - Once completed, click `manage keys and access tokens` next to your Consumer Key
 - Click 'Create Access Token' towards the bottom of the page
 - Copy your consumer key and secret as well as your access token and secret into the `config.cfg` file (note: these values do not require quotes around them. Be sure to not check in or share this file!)
 - Create a text file listing all of the Twitter accounts you'd like to pull images from, each account on a new line (see `chicago.txt` for an example)
 - Run the script: `python grab_socmint.py <your_file_name.txt>`
 - Images should appear in 'pictures' directory

 Additional notes:
 - If you run into KeyErrors, the `src/run.py` script from `downloadTwitterPictures` cannot find your config file: easy fix is to explicitly define the file's path by changing the `config.read` line in the `parse_config` function to be `config.read(os.path.join(os.path.dirname(__file__), config_file))`
 - Script will default to reading from `chicago.txt` if no filename is provided
