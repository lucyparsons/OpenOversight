import os


# Encoding constants
ENCODING_UTF_8 = "utf-8"

# HTTP Method constants
# TODO: Remove these constants and use HTTPMethod in http package when we
#  migrate to version 3.11
HTTP_METHOD_GET = "GET"
HTTP_METHOD_POST = "POST"

# Ensure the file is read/write by the creator only
SAVED_UMASK = os.umask(0o077)
