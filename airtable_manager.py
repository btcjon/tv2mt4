from airtable import Airtable
import config

class AirtableManager:
    def __init__(self):
        self.airtable = Airtable(config.AIRTABLE_BASE_ID, config.AIRTABLE_TABLE_NAME, api_key=config.AIRTABLE_API_KEY)

    def get_matching_record(self, symbol):
        symbol_without_pro = symbol.replace('.PRO', '')
        records = self.airtable.get_all(formula=f"{{Symbol}} = '{symbol_without_pro}'")
        return records[0] if records else None

    def update_trend(self, symbol, trend, logger):
        record = self.get_matching_record(symbol)
        logger.debug(f"Updating trend for {symbol} to {trend}")
        if record:
            response = self.airtable.update(record['id'], {'Trend': trend})
            logger.debug(f"Airtable update response: {response}")

    def update_snr(self, symbol, snr, logger):
        record = self.get_matching_record(symbol)
        logger.debug(f"Updating SnR for {symbol} to {snr}")
        if record:
            response = self.airtable.update(record['id'], {'SnR': snr})
            logger.debug(f"Airtable update response: {response}")

    def update_state(self, symbol, state, command, logger):
        record = self.get_matching_record(symbol)
        state_field = 'State Long' if command == 'long' else 'State Short'
        logger.debug(f"Updating {state_field} for {symbol} to {state}")
        if record:
            response = self.airtable.update(record['id'], {state_field: state})
            logger.debug(f"Airtable update response: {response}")

    def update_count(self, symbol, command, logger):
        record = self.get_matching_record(symbol)
        count_field = 'Count Long' if command == 'long' else 'Count Short'
        if record:
            count = record['fields'].get(count_field, '-')
            count = '0' if count == '-' else str(int(count) + 1)
            response = self.airtable.update(record['id'], {count_field: count})
            logger.debug(f"Airtable update response: {response}")
