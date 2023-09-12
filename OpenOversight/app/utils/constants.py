import os


# Cache Key Constants
KEY_DEPT_ALL_ASSIGNMENTS = "all_department_assignments"
KEY_DEPT_ALL_INCIDENTS = "all_department_incidents"
KEY_DEPT_ALL_LINKS = "all_department_links"
KEY_DEPT_ALL_NOTES = "all_department_notes"
KEY_DEPT_ALL_OFFICERS = "all_department_officers"
KEY_DEPT_ALL_SALARIES = "all_department_salaries"
KEY_DEPT_TOTAL_ASSIGNMENTS = "total_department_assignments"
KEY_DEPT_TOTAL_INCIDENTS = "total_department_incidents"
KEY_DEPT_TOTAL_OFFICERS = "total_department_officers"

# Config Key Constants
KEY_ALLOWED_EXTENSIONS = "ALLOWED_EXTENSIONS"
KEY_DATABASE_URI = "SQLALCHEMY_DATABASE_URI"
KEY_ENV = "ENV"
KEY_ENV_DEV = "development"
KEY_ENV_TESTING = "testing"
KEY_ENV_PROD = "production"
KEY_NUM_OFFICERS = "NUM_OFFICERS"
KEY_OFFICERS_PER_PAGE = "OFFICERS_PER_PAGE"
KEY_OO_MAIL_SUBJECT_PREFIX = "OO_MAIL_SUBJECT_PREFIX"
KEY_OO_HELP_EMAIL = "OO_HELP_EMAIL"
KEY_OO_SERVICE_EMAIL = "OO_SERVICE_EMAIL"
KEY_MAIL_SERVER = "MAIL_SERVER"
KEY_MAIL_PORT = "MAIL_PORT"
KEY_MAIL_USE_TLS = "MAIL_USE_TLS"
KEY_MAIL_USERNAME = "MAIL_USERNAME"
KEY_MAIL_PASSWORD = "MAIL_PASSWORD"
KEY_S3_BUCKET_NAME = "S3_BUCKET_NAME"
KEY_TIMEZONE = "TIMEZONE"

# Database Key Constants
KEY_DB_CREATOR = "creator"

# DateTime Constants
OO_DATE_FORMAT = "%b %d, %Y"
OO_TIME_FORMAT = "%I:%M %p"

# File Handling Constants
ENCODING_UTF_8 = "utf-8"
FILE_TYPE_HTML = "html"
FILE_TYPE_PLAIN = "plain"
SAVED_UMASK = os.umask(0o077)  # Ensure the file is read/write by the creator only

# File Name Constants
SERVICE_ACCOUNT_FILE = "service_account_key.json"

# JWT Constants
SIGNATURE_ALGORITHM = "HS512"

# Numerical Constants
BYTE = 1
KILOBYTE = 1024 * BYTE
MEGABYTE = 1024 * KILOBYTE
MINUTE = 60
HOUR = 60 * MINUTE

# UI Constants
FIELD_NOT_AVAILABLE = "Field Not Available"
FLASH_MSG_PERMANENT_REDIRECT = (
    "This page's address has changed, please update your bookmark!"
)
