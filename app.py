from flask import Flask, request
import logging
import requests
import config
from datetime import datetime, time
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
                response = self.airtable.update(record['id'], {field: value})
                self.logger.info(f"Successfully updated {field} for {symbol} to {value}")
            else:
                self.logger.warning(f"No matching record found for symbol: {symbol}")
        except Exception as e:
            self.logger.error(f"Failed to update {field} for {symbol} to {value}: {e}")

    def increment_airtable_field(self, symbol, field):
        try:
            record = self.get_matching_record(symbol)
            if record:
                count = record['fields'].get(field, '0')
                count = str(int(count) + 1)
                response = self.airtable.update(record['id'], {field: count})
                self.logger.info(f"Successfully incremented {field} for {symbol} by 1")
            else:
                self.logger.warning(f"No matching record found for symbol: {symbol}")
        except Exception as e:
            self.logger.error(f"Failed to increment {field} for {symbol}: {e}")

    def reset_airtable_field(self, symbol, field):
        record = self.get_matching_record(symbol)
        if record:
            response = self.airtable.update(record['id'], {field: '0'})
            self.logger.debug(f"Airtable update response: {response}")

airtable_operations = AirtableOperations()

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.data.decode('utf-8')
        app.logger.debug(f"Received webhook data: {data}")
        parts = data.split(',')

        message_dict = {part.split('=')[0]: part.split('=')[1] for part in parts}
        message_type = message_dict.get('type')
        symbol = message_dict.get('symbol')

        if message_type == 'update':
            try:
                keyword = message_dict.get('keyword')
                if keyword in ['resistance', 'support', 'TD9buy', 'TD9sell', 'resistanceOFF', 'supportOFF', 'TD9sellOff', 'up', 'down']:
                    update_value = not keyword.endswith('OFF')
                    field_name = keyword.replace('Off', '')
                    airtable_operations.update_airtable_field(symbol, field_name, update_value)
                app.logger.info(f"Processed update message for symbol: {symbol}")
            except Exception as e:
                app.logger.error(f"Failed to process update message for symbol: {symbol}: {e}")
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
                return  # If it is, do not send any commands to PineConnector

            if order_type in ['closelong', 'closeshort']:
                send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)
            else:
                record = airtable_operations.get_matching_record(symbol)
                if record:
                    bb_present = record['fields'].get('BB')  # get the BB field
                    if bb_present:
                        app.logger.info(f"Order for {symbol} filtered: BB is present")
                        return  # if BB is present, do not send command to PineConnector

                    state_field = 'State Long' if order_type == 'long' else 'State Short'
                    state = record['fields'].get(state_field)
                    trend = record['fields'].get('Trend')
                    snr = record['fields'].get('SnR')

                    if order_type == "long" and trend != "up":
                        app.logger.info(f"Order for {symbol} filtered: Trend is not up")
                    if order_type == "long" and snr == "Resistance":
                        app.logger.info(f"Order for {symbol} filtered: SnR is Resistance")

                    if (order_type == "long" and trend == "up" and snr != "Resistance") or (order_type == "short" and trend == "down" and snr != "Support"):
                        send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)

            # Add the check for Long# and Short# fields being greater than '0'
            if order_type in ['long', 'short']:
                record = airtable_operations.get_matching_record(symbol)
                if record:
                    count_field = f'{order_type.capitalize()}#'
                    count = record['fields'].get(count_field, '0')
                    if int(count) > 0:
                        send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)
                    # Existing checks for trend, resistance, support, and TD9 indicators
                    # ... (This comment should be followed by the actual checks or removed if not applicable)
                    airtable_operations.update_airtable_field(symbol, f'State {order_type.capitalize()}', 'open')
                    airtable_operations.increment_airtable_field(symbol, count_field)
                elif order_type in ['closelong', 'closeshort']:
                        airtable_operations.update_airtable_field(symbol, f'State {order_type[5:].capitalize()}', 'closed')
                        airtable_operations.reset_airtable_field(symbol, f'{order_type[5:].capitalize()}#')

            return '', 200

    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return 'Error', 500
    
    return '', 200

def send_pineconnector_command(order_type, symbol, risk, tp, sl, comment):
    pineconnector_command = f"{config.PINECONNECTOR_LICENSE_ID},{order_type},{symbol}"
    if risk:
        pineconnector_command += f",risk={risk}"
    if tp:
        pineconnector_command += f",tp={tp}"
    if sl:
        pineconnector_command += f",sl={sl}"
    if comment:
        pineconnector_command += f",comment=\"{comment}\""
    app.logger.debug(f"Sending PineConnector command: {pineconnector_command}")
    response = requests.post(config.PINECONNECTOR_WEBHOOK_URL, data=pineconnector_command)
    app.logger.debug(f"PineConnector response: {response.text}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
