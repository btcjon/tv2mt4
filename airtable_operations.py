# airtable_operations.py
from airtable import Airtable
import config
import logging

class AirtableOperations:
    def __init__(self):
        self.airtable = Airtable(config.AIRTABLE_BASE_ID, config.AIRTABLE_TABLE_NAME, api_key=config.AIRTABLE_API_KEY)
        self.logger = logging.getLogger(__name__)

    def get_matching_record(self, symbol):
        symbol_without_pro = symbol.replace('.PRO', '')
        records = self.airtable.get_all(formula=f"{{Symbol}} = '{symbol_without_pro}'")
        return records[0] if records else None

    def update_airtable_trend(self, symbol, trend):
        record = self.get_matching_record(symbol)
        self.logger.debug(f"Updating trend for {symbol} to {trend}")
        if record:
            response = self.airtable.update(record['id'], {'Trend': trend})
            self.logger.debug(f"Airtable update response: {response}")

    def update_airtable_snr(self, symbol, snr):
        record = self.get_matching_record(symbol)
        self.logger.debug(f"Updating SnR for {symbol} to {snr}")
        if record:
            response = self.airtable.update(record['id'], {'SnR': snr})
            self.logger.debug(f"Airtable update response: {response}")
    
    def update_airtable_td9buy(self, symbol, status):
        record = self.get_matching_record(symbol)
        self.logger.debug(f"Updating '1H TD9buy' for {symbol} to {status}")
        if record:
            response = self.airtable.update(record['id'], {'1H TD9buy': str(status).lower()})
            self.logger.debug(f"Airtable update response: {response}")

    def update_airtable_td9buy(self, symbol, status):
        record = self.get_matching_record(symbol)
        self.logger.debug(f"Updating '1H TD9buy' for {symbol} to {status}")
        if record:
            status_bool = status.lower() == 'true'
            response = self.airtable.update(record['id'], {'1H TD9buy': status_bool})
            self.logger.debug(f"Airtable update response: {response}")

    def update_airtable_td9sell(self, symbol, status):
        record = self.get_matching_record(symbol)
        self.logger.debug(f"Updating '1H TD9sell' for {symbol} to {status}")
        if record:
            status_bool = status.lower() == 'true'
            response = self.airtable.update(record['id'], {'1H TD9sell': status_bool})
            self.logger.debug(f"Airtable update response: {response}")

    def update_airtable_count(self, symbol, command):
        record = self.get_matching_record(symbol)
        count_field = 'Count Long' if command == 'long' else 'Count Short'
        if record:
            count = record['fields'].get(count_field, '-')
            count = '0' if count == '-' else str(int(count) + 1)
            response = self.airtable.update(record['id'], {count_field: count})
            self.logger.debug(f"Airtable update response: {response}")
