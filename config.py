# config.py
import yaml

# Load patterns from YAML configuration file
with open('patterns.yaml', 'r') as file:
    PATTERNS = yaml.safe_load(file)

AIRTABLE_API_KEY = 'key8E4aVpJpRArGyw'
AIRTABLE_BASE_ID = 'app2hV8yClkObvn6v'
AIRTABLE_TABLE_NAME = 'table1'
NGROK_AUTH_TOKEN = '2RQAN658II3AIdb9t09ogLi1wJ4_2JATXbhEEYRhzrSuJraBv'
PINECONNECTOR_WEBHOOK_URL = 'https://pineconnector.net/webhook/'
LICENSE_ID = '6700960415957'
CHECK_STATE = True
