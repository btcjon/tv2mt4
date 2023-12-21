
import requests
from datetime import datetime, time
import config
import logging
from airtable import Airtable

class AirtableOperations:
    def __init__(self):
        self.airtable = Airtable(config.AIRTABLE_BASE_ID, config.AIRTABLE_TABLE_NAME, api_key=config.AIRTABLE_API_KEY)
        self.logger = logging.getLogger(__name__)

    def get_matching_record(self, symbol):
        symbol_without_pro = symbol.replace('.PRO', '')
        records = self.airtable.get_all(formula=f"{{Symbol}} = '{symbol_without_pro}'")
        return records[0] if records else None

    def update_airtable_field(self, symbol, field, value):
        try:
            record = self.get_matching_record(symbol)
            action = 'update' if value not in [False, None] else 'clear'
            self.logger.debug(f"Attempting to {action} {field} for {symbol} to {value}")
            if record:
                self.airtable.update(record['id'], {field: value})
                self.logger.info(f"Successfully {action}d {field} for {symbol} to {value} in Airtable")
            else:
                self.logger.warning(f"No matching record found for symbol: {symbol}")
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error when updating {field} for {symbol} to {value}: {e}, retrying...")
            time.sleep(5)  # Wait for 5 seconds before retrying
            try:
                response = self.airtable.update(record['id'], {field: value})
                self.logger.info(f"Successfully {action}d {field} for {symbol} to {value} on retry in Airtable")
            except Exception as retry_e:
                self.logger.error(f"Failed to update {field} for {symbol} to {value} on retry: {retry_e}")
        except Exception as e:
            self.logger.error(f"Failed to update {field} for {symbol} to {value}: {e}")

    def increment_airtable_field(self, symbol, field):
        try:
            record = self.get_matching_record(symbol)
            if record:
                count = record['fields'].get(field, 0)  # Ensure the default value is an integer 0
                count = int(count) + 1
                try:
                    self.airtable.update(record['id'], {field: count})  # Send an integer value
                    self.logger.info(f"Successfully incremented {field} for {symbol} by 1 in Airtable")
                except requests.exceptions.HTTPError as http_err:
                    self.logger.error(f"HTTP error occurred when incrementing {field} for {symbol}: {http_err.response.text}")
                except Exception as e:
                    self.logger.error(f"Failed to increment {field} for {symbol}: {e}")
            else:
                self.logger.warning(f"No matching record found for symbol: {symbol}")
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error occurred when incrementing {field} for {symbol}: {http_err}")
        except Exception as e:
            self.logger.error(f"Failed to increment {field} for {symbol}: {e}")

    def reset_airtable_field(self, symbol, field):
        try:
            record = self.get_matching_record(symbol)
            if record:
                self.airtable.update(record['id'], {field: 0})  # Send an integer value for the reset
                self.logger.info(f"Successfully reset {field} for {symbol} in Airtable")
            else:
                self.logger.warning(f"No matching record found for symbol: {symbol}")
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error occurred when resetting {field} for {symbol}: {http_err}")
        except Exception as e:
            self.logger.error(f"Failed to reset {field} for {symbol}: {e}")

airtable_operations = AirtableOperations()
