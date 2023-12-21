import logging
import requests
import time
from airtable import Airtable
import config

class AirtableOperations:
    def __init__(self):
        self.airtable = Airtable(config.AIRTABLE_BASE_ID, config.AIRTABLE_TABLE_NAME, api_key=config.AIRTABLE_API_KEY)
        self.logger = logging.getLogger(__name__)
        self.logger.propagate = False

    # ... all the methods from AirtableOperations class ...
import logging
import requests
import time
from airtable import Airtable
import config

class AirtableOperations:
    def __init__(self):
        self.airtable = Airtable(config.AIRTABLE_BASE_ID, config.AIRTABLE_TABLE_NAME, api_key=config.AIRTABLE_API_KEY)
        self.logger = logging.getLogger(__name__)
        self.logger.propagate = False

    # ... all the methods from AirtableOperations class ...
