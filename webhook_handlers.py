from flask import request
from datetime import datetime
import config
from airtable_operations import AirtableOperations
from utils import send_pineconnector_command
import logging

def webhook():
    try:
        data = request.data.decode('utf-8')
        # Removed redundant debug log for received data
        parts = data.split(',')

        # Only include parts that can be split into exactly two items with '='
        message_dict = {part.split('=')[0]: part.split('=')[1] for part in parts if '=' in part and len(part.split('=')) == 2}
        message_type = message_dict.get('type')
        symbol = message_dict.get('symbol')
        entry = message_dict.get('entry', 'true').lower() == 'true'  # Default to true if not specified
        if symbol in ['NAS100', 'NAS100.PRO']:
            symbol = 'USTEC100'

        if message_type == 'update':
            # ... [The rest of the update logic from app_old.py] ...
        elif message_type == 'order':
            # ... [The rest of the order logic from app_old.py] ...
            # ... [Including all the conditions and Airtable field updates] ...

    except Exception as e:
        logging.exception("Error handling webhook", exc_info=e)
        return 'Error', 500
