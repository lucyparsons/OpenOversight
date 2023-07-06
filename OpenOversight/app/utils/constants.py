import os


# Encoding constants
ENCODING_UTF_8 = "utf-8"

# Ensure the file is read/write by the creator only
SAVED_UMASK = os.umask(0o077)
