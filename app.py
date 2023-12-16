import re
from flask import Flask, request
import logging
import requests
import config
from datetime import datetime
from datetime import time
from airtable import Airtable

app = Flask(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

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
            self.logger.debug(f"Attempting to update {field} for {symbol} to {value}")
            if record:
                self.airtable.update(record['id'], {field: value})
                self.logger.info(f"Successfully updated {field} for {symbol} to {value}")
            else:
                self.logger.warning(f"No matching record found for symbol: {symbol}")
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error when updating {field} for {symbol} to {value}: {e}, retrying...")
            time.sleep(5)  # Wait for 5 seconds before retrying
            try:
                response = self.airtable.update(record['id'], {field: value})
                self.logger.info(f"Successfully updated {field} for {symbol} to {value} on retry")
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
                    self.logger.info(f"Successfully incremented {field} for {symbol} by 1")
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
                self.logger.info(f"Successfully reset {field} for {symbol}")
            else:
                self.logger.warning(f"No matching record found for symbol: {symbol}")
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error occurred when resetting {field} for {symbol}: {http_err}")
        except Exception as e:
            self.logger.error(f"Failed to reset {field} for {symbol}: {e}")

airtable_operations = AirtableOperations()

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.data.decode('utf-8')
        app.logger.debug(f"Received webhook data: {data}")

        # Check if the message starts with an ID and an order type
        if re.match(r'^\d+,(long|short|closelong|closeshort),', data):
            # Handle the new message format
            parse_new_order_format(data)
            return '', 200
        else:
            # Handle the old message format
            parts = data.split(',')

            # Only include parts that can be split into exactly two items with '='
            message_dict = {part.split('=')[0]: part.split('=')[1] for part in parts if '=' in part and len(part.split('=')) == 2}
            message_type = message_dict.get('type')
            symbol = message_dict.get('symbol')
            # ... (rest of the existing code remains unchanged)

        parts = data.split(',')

        # Only include parts that can be split into exactly two items with '='
        message_dict = {part.split('=')[0]: part.split('=')[1] for part in parts if '=' in part and len(part.split('=')) == 2}
        message_type = message_dict.get('type')
        symbol = message_dict.get('symbol')
        if symbol in ['NAS100', 'NAS100.PRO']:
            symbol = 'USTEC100'

        if message_type == 'update':
            keyword = message_dict.get('keyword')
            field_name = None
            update_value = None
            if keyword == 'resistance':
                field_name = 'Resistance'
                update_value = True
            elif keyword == 'resistanceOFF':
                field_name = 'Resistance'
                update_value = False
            elif keyword == 'support':
                field_name = 'Support'
                update_value = True
            elif keyword == 'supportOFF':
                field_name = 'Support'
                update_value = False
            elif keyword == 'TD9buy':
                field_name = 'TD9buy'
                update_value = True
            elif keyword == 'TD9buyOFF':
                field_name = 'TD9buy'
                update_value = False
            elif keyword == 'TD9sell':
                field_name = 'TD9sell'
                update_value = True
            elif keyword == 'TD9sellOFF':  # Corrected keyword
                field_name = 'TD9sell'
                update_value = False
            elif keyword == 'up':
                field_name = 'Trend'
                update_value = 'up'
            elif keyword == 'down':
                field_name = 'Trend'
                update_value = 'down'
            try:
                if field_name is not None and update_value is not None:
                    airtable_operations.update_airtable_field(symbol, field_name, update_value)
                    app.logger.info(f"Processed update message for symbol: {symbol}")
                else:
                    app.logger.error(f"Unrecognized keyword in update message for symbol: {symbol}: {keyword}")
                return '', 200
            except Exception as e:
                app.logger.exception(f"An exception occurred while processing the update message for symbol: {symbol}: {e}")
                return 'Error', 500
        elif message_type == 'order':
            order_type = message_dict.get('order-type')
            risk = message_dict.get('risk')
            tp = message_dict.get('tp')
            sl = message_dict.get('sl')
            comment = message_dict.get('comment')

            # Get the current server time
            now = datetime.utcnow().time()

            # Define the start and end of the restricted period in UTC
            start = time(21, 55)  # 9:55 PM UTC
            end = time(23, 0)  # 11:00 PM UTC

            # Check if the current time is within the restricted period
            if start <= now <= end:
                if config.FILTER_TIME:
                    app.logger.info(f"Order for {symbol} not sent due to time restriction.")
                    return '', 200  # If it is, do not send any commands to PineConnector

            record = airtable_operations.get_matching_record(symbol)
            if record:
                bb_present = record['fields'].get('BB')  # get the BB field
                if bb_present:
                    app.logger.info(f"Order for {symbol} filtered: BB is present")
                    return '', 200  # if BB is present, do not send command to PineConnector

            # Check for closelong and closeshort order types
            if order_type in ['closelong', 'closeshort']:
                # Get the current server time
                now = datetime.utcnow().time()

                # Define the start and end of the restricted period in UTC
                start = time(21, 55)  # 9:55 PM UTC
                end = time(23, 0)  # 11:00 PM UTC

                # Check if the current time is within the restricted period
                if start <= now <= end and config.FILTER_TIME:
                    app.logger.info(f"Order for {symbol} not sent due to time restriction.")
                    return '', 200  # If it is, do not send any commands to PineConnector

                # Check for BB (State) restriction
                state_field = 'State Long' if order_type == 'closelong' else 'State Short'
                record = airtable_operations.get_matching_record(symbol)
                if record and record['fields'].get(state_field) == 'BB':
                    app.logger.info(f"Order for {symbol} not sent due to BB restriction.")
                    return '', 200  # If BB is present, do not send command to PineConnector

                # If both checks pass, send the command to PineConnector
                send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)
                airtable_operations.update_airtable_field(symbol, f'State {order_type[5:].capitalize()}', 'closed')
                airtable_operations.reset_airtable_field(symbol, f'{order_type[5:].capitalize()}#')
            if order_type == 'long':
                long_count = int(record['fields'].get('Long#', 0))
                trend = record['fields'].get('Trend')
                resistance = record['fields'].get('Resistance', False)
                td9sell = record['fields'].get('TD9sell', False)
                # Check if Long# is greater than 0 or if trend is up and no resistance or TD9sell signal is present
                if long_count > 0 or (trend == 'up' and not resistance and not td9sell):
                    send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)
                    if long_count == 0:  # Only update if Long# was 0
                        airtable_operations.update_airtable_field(symbol, 'State Long', 'open')
                        airtable_operations.increment_airtable_field(symbol, 'Long#')
            elif order_type == 'short':
                short_count = int(record['fields'].get('Short#', 0))
                trend = record['fields'].get('Trend')
                support = record['fields'].get('Support', False)
                td9buy = record['fields'].get('TD9buy', False)
                # Check if Short# is greater than 0 or if trend is down and no support or TD9buy signal is present
                if short_count > 0 or (trend == 'down' and not support and not td9buy):
                    send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)
                    if short_count == 0:  # Only update if Short# was 0
                        airtable_operations.update_airtable_field(symbol, 'State Short', 'open')
                        airtable_operations.increment_airtable_field(symbol, 'Short#')
            elif order_type in ['closelong', 'closeshort']:
                send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)
                airtable_operations.update_airtable_field(symbol, f'State {order_type[5:].capitalize()}', 'closed')
                airtable_operations.reset_airtable_field(symbol, f'{order_type[5:].capitalize()}#')

            return '', 200

    except Exception as e:
        app.logger.exception(f"An unhandled exception occurred in the webhook function: {e}")
        return 'Error', 500

def send_pineconnector_command(order_id, order_type, symbol, risk=None, tp=None, sl=None, comment=None):
    # Format the PineConnector command based on the provided parameters, including the order ID
    command_parts = [order_id, order_type, symbol]
    if risk:
        command_parts.append(f"risk={risk}")
    if tp:
        command_parts.append(f"tp={tp}")
    if sl:
        command_parts.append(f"sl={sl}")
    if comment:
        command_parts.append(f'comment="{comment}"')  # Ensure the comment is enclosed in quotes
    pineconnector_command = ','.join(command_parts)
    app.logger.debug(f"Sending PineConnector command: {pineconnector_command}")
    # Send the command to PineConnector
    response = requests.post(config.PINECONNECTOR_WEBHOOK_URL, data=pineconnector_command.encode('utf-8'))
    app.logger.debug(f"PineConnector response: {response.text}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
def parse_new_order_format(data):
    # Use regular expression to parse the new order format
    match = re.match(r'^(\d+),(long|short|closelong|closeshort),([^,]+)(,.+)?$', data)
    if match:
        order_id = match.group(1)
        order_type = match.group(2)
        symbol = match.group(3)
        # Initialize optional parameters
        risk = None
        tp = None
        sl = None
        comment = None
        # Extract the optional parameters if present
        optional_params = match.group(4)
        if optional_params:
            optional_parts = optional_params.split(',')
            for part in optional_parts:
                if '=' in part:
                    key, value = part.split('=')
                    if key == 'risk':
                        risk = value
                    elif key == 'tp':
                        tp = value
                    elif key == 'sl':
                        sl = value
                    elif key == 'comment':
                        comment = value.strip('”"')  # Remove any quotation marks
        # Call the send_pineconnector_command function with the extracted information and include the order ID
        send_pineconnector_command(order_id, order_type, symbol, risk, tp, sl, comment)
