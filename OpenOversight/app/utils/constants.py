import os


# Cache Key Constants
KEY_TOTAL_ASSIGNMENTS = "total_assignments"
KEY_TOTAL_INCIDENTS = "total_incidents"
KEY_TOTAL_OFFICERS = "total_officers"

# Config Key Constants
KEY_OFFICERS_PER_PAGE = "OFFICERS_PER_PAGE"
KEY_TIMEZONE = "TIMEZONE"

# File Handling Constants
ENCODING_UTF_8 = "utf-8"
SAVED_UMASK = os.umask(0o077)  # Ensure the file is read/write by the creator only

# File Name Constants
SERVICE_ACCOUNT_FILE = "service_account_key.json"

# Numerical Constants
BYTE = 1
KILOBYTE = 1024 * BYTE
MEGABYTE = 1024 * KILOBYTE
MINUTE = 60
HOUR = 60 * MINUTE
