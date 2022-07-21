""" Stores settings using python-dotenv. This file can be included in version
control and contains references to environment variables but checks
if the variable is present in a .env file (which is not included in
version control) and uses those values first

Every variable should be included here even it is not present in Environment
variables.

example

API_TOKEN = os.getenv(".ENV_API_TOKEN")

"""

import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("DB_CSV_API_TOKEN")
ENDPOINT = os.getenv("ENDPOINT")
TENANT = os.getenv("TENANT")
