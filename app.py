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

def send_pineconnector_command(order_type, symbol, risk, tp, sl, comment):
    if not symbol.endswith('.PRO') and symbol != 'USTEC100':
        symbol += '.PRO'  # append '.PRO' to the symbol only if it's not already there
    pineconnector_command = f"{config.PINECONNECTOR_LICENSE_ID},{order_type},{symbol}"
    if risk:
        pineconnector_command += f",risk={risk}"
    if tp:
        pineconnector_command += f",tp={tp}"
    if sl:
        pineconnector_command += f",sl={sl}"
    if comment:
        # Directly append the comment without additional quotes
        pineconnector_command += f',comment={comment}'
    app.logger.debug(f"Sending PineConnector command: {pineconnector_command}")
    response = requests.post(config.PINECONNECTOR_WEBHOOK_URL, data=pineconnector_command)
    app.logger.debug(f"PineConnector response: {response.text}")


@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.data.decode('utf-8')
        app.logger.debug(f"Received webhook data: {data}")
        parts = data.split(',')

        # Extract the order type and symbol from the data
        order_type = parts[1].strip()
        symbol = parts[2].strip()

        # Check if the order type is 'long' or 'short'
        if order_type in ['long', 'short']:
            risk = parts[3].split('=')[1] if 'risk' in parts[3] else None
            comment = parts[4].split('=')[1] if 'comment' in parts[4] else None

            # Get the current server time
            now = datetime.utcnow().time()

            # Define the start and end of the restricted period in UTC
            start = time(21, 55)  # 9:55 PM UTC
            end = time(23, 0)  # 11:00 PM UTC

            # Check if the current time is within the restricted period
            if start <= now <= end:
                return '', 200  # If it is, do not send any commands to PineConnector

            record = airtable_operations.get_matching_record(symbol)
            if record:
                bb_present = record['fields'].get('BB')  # get the BB field
                if bb_present:
                    app.logger.info(f"Order for {symbol} filtered: BB is present")
                    return '', 200  # if BB is present, do not send command to PineConnector

                trend = record['fields'].get('Trend')
                if (order_type == 'long' and trend != 'up') or (order_type == 'short' and trend != 'down'):
                    app.logger.info(f"Order for {symbol} filtered: Trend is not correct")
                    return '', 200  # if trend is not correct, do not send command to PineConnector

                # If checks pass, send command to PineConnector
                send_pineconnector_command(order_type, symbol, risk, None, None, comment)

        else:
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
                    return '', 200  # If it is, do not send any commands to PineConnector

                record = airtable_operations.get_matching_record(symbol)
                if record:
                    bb_present = record['fields'].get('BB')  # get the BB field
                    if bb_present:
                        app.logger.info(f"Order for {symbol} filtered: BB is present")
                        return '', 200  # if BB is present, do not send command to PineConnector

                if order_type in ['closelong', 'closeshort']:
                    send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)

                    state_field = 'State Long' if order_type == 'long' else 'State Short'
                    state = record['fields'].get(state_field)
                    trend = record['fields'].get('Trend')
                    snr = record['fields'].get('SnR')

                if config.FILTER_SNR and order_type == "short" and snr == "Support":
                    app.logger.info(f"Order for {symbol} filtered: SnR is Support")
                elif config.FILTER_STATE and state != "Ready":
                    app.logger.info(f"Order for {symbol} filtered: State is not Ready")
                elif config.FILTER_TREND and ((order_type == "long" and trend != "up") or (order_type == "short" and trend != "down")):
                    app.logger.info(f"Order for {symbol} filtered: Trend is not correct")
                else:
                    send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)
                return '', 200

    except Exception as e:
        app.logger.exception(f"An unhandled exception occurred in the webhook function: {e}")
        return 'Error', 500

                   





#my old  code
# @app.route('/webhook', methods=['POST'])
# def webhook():
#     try:
#         data = request.data.decode('utf-8')
#         app.logger.debug(f"Received webhook data: {data}")
#         parts = data.split(',')

#         # Only include parts that can be split into exactly two items with '='
#         message_dict = {part.split('=')[0]: part.split('=')[1] for part in parts if '=' in part and len(part.split('=')) == 2}
#         message_type = message_dict.get('type')
#         symbol = message_dict.get('symbol')
#         if symbol in ['NAS100', 'NAS100.PRO']:
#             symbol = 'USTEC100'

#         if message_type == 'update':
#             keyword = message_dict.get('keyword')
#             field_name = None
#             update_value = None
#             if keyword == 'resistance':
#                 field_name = 'Resistance'
#                 update_value = True
#             elif keyword == 'resistanceOFF':
#                 field_name = 'Resistance'
#                 update_value = False
#             elif keyword == 'support':
#                 field_name = 'Support'
#                 update_value = True
#             elif keyword == 'supportOFF':
#                 field_name = 'Support'
#                 update_value = False
#             elif keyword == 'TD9buy':
#                 field_name = 'TD9buy'
#                 update_value = True
#             elif keyword == 'TD9buyOFF':
#                 field_name = 'TD9buy'
#                 update_value = False
#             elif keyword == 'TD9sell':
#                 field_name = 'TD9sell'
#                 update_value = True
#             elif keyword == 'TD9sellOFF':  # Corrected keyword
#                 field_name = 'TD9sell'
#                 update_value = False
#             elif keyword == 'up':
#                 field_name = 'Trend'
#                 update_value = 'up'
#             elif keyword == 'down':
#                 field_name = 'Trend'
#                 update_value = 'down'
#             try:
#                 if field_name is not None and update_value is not None:
#                     airtable_operations.update_airtable_field(symbol, field_name, update_value)
#                     app.logger.info(f"Processed update message for symbol: {symbol}")
#                 else:
#                     app.logger.error(f"Unrecognized keyword in update message for symbol: {symbol}: {keyword}")
#                 return '', 200
#             except Exception as e:
#                 app.logger.exception(f"An exception occurred while processing the update message for symbol: {symbol}: {e}")
#                 return 'Error', 500
#         elif message_type == 'order':
#             order_type = message_dict.get('order-type')
#             risk = message_dict.get('risk')
#             tp = message_dict.get('tp')
#             sl = message_dict.get('sl')
#             comment = message_dict.get('comment')

#             # Get the current server time
#             now = datetime.utcnow().time()

#             # Define the start and end of the restricted period in UTC
#             start = time(21, 55)  # 9:55 PM UTC
#             end = time(23, 0)  # 11:00 PM UTC

#             # Check if the current time is within the restricted period
#             if start <= now <= end:
#                 return '', 200  # If it is, do not send any commands to PineConnector

#             record = airtable_operations.get_matching_record(symbol)
#             if record:
#                 bb_present = record['fields'].get('BB')  # get the BB field
#                 if bb_present:
#                     app.logger.info(f"Order for {symbol} filtered: BB is present")
#                     return '', 200  # if BB is present, do not send command to PineConnector

#             if order_type in ['closelong', 'closeshort']:
#                 send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)

#                 state_field = 'State Long' if order_type == 'long' else 'State Short'
#                 state = record['fields'].get(state_field)
#                 trend = record['fields'].get('Trend')
#                 snr = record['fields'].get('SnR')

#                 if config.FILTER_SNR and order_type == "long" and snr == "Resistance":
#                     app.logger.info(f"Order for {symbol} filtered: SnR is Resistance")

#                 td9sell_present = record['fields'].get('TD9sell')  # get the TD9sell field for long orders
#                 td9buy_present = record['fields'].get('TD9buy')  # get the TD9buy field for short orders

#                 if config.FILTER_TD9 and order_type == "long" and td9sell_present:
#                     app.logger.info(f"Order for {symbol} filtered: TD9sell is present")

#                 if config.FILTER_TREND and order_type == "long" and trend != "up":
#                     app.logger.info(f"Order for {symbol} filtered: Trend is not up")

#                 if order_type == "long" and trend == "up" and not td9sell_present and snr != "Resistance":
#                     send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)
#                 elif order_type == "short" and trend == "down" and not td9buy_present and snr != "Support":
#                     send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)

#             # Add the check for Long# and Short# fields being greater than '0'
#             if order_type == 'long':
#                 long_count = int(record['fields'].get('Long#', 0))
#                 trend = record['fields'].get('Trend')
#                 resistance = record['fields'].get('Resistance', False)
#                 td9sell = record['fields'].get('TD9sell', False)
#                 # Check if Long# is greater than 0 or if trend is up and no resistance or TD9sell signal is present
#                 if long_count > 0 or (trend == 'up' and not resistance and not td9sell):
#                     send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)
#                     if long_count == 0:  # Only update if Long# was 0
#                         airtable_operations.update_airtable_field(symbol, 'State Long', 'open')
#                         airtable_operations.increment_airtable_field(symbol, 'Long#')
#             elif order_type == 'short':
#                 short_count = int(record['fields'].get('Short#', 0))
#                 trend = record['fields'].get('Trend')
#                 support = record['fields'].get('Support', False)
#                 td9buy = record['fields'].get('TD9buy', False)
#                 # Check if Short# is greater than 0 or if trend is down and no support or TD9buy signal is present
#                 if short_count > 0 or (trend == 'down' and not support and not td9buy):
#                     send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)
#                     if short_count == 0:  # Only update if Short# was 0
#                         airtable_operations.update_airtable_field(symbol, 'State Short', 'open')
#                         airtable_operations.increment_airtable_field(symbol, 'Short#')
#             elif order_type in ['closelong', 'closeshort']:
#                 send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)
#                 airtable_operations.update_airtable_field(symbol, f'State {order_type[5:].capitalize()}', 'closed')
#                 airtable_operations.reset_airtable_field(symbol, f'{order_type[5:].capitalize()}#')

#             return '', 200

#     except Exception as e:
#         app.logger.exception(f"An unhandled exception occurred in the webhook function: {e}")
#         return 'Error', 500

# def send_pineconnector_command(order_type, symbol, risk, tp, sl, comment):
#     if not symbol.endswith('.PRO') and symbol != 'USTEC100':
#         symbol += '.PRO'  # append '.PRO' to the symbol only if it's not already there
#     pineconnector_command = f"{config.PINECONNECTOR_LICENSE_ID},{order_type},{symbol}"
#     if risk:
#         pineconnector_command += f",risk={risk}"
#     if tp:
#         pineconnector_command += f",tp={tp}"
#     if sl:
#         pineconnector_command += f",sl={sl}"
#     if comment:
#         # Directly append the comment without additional quotes
#         pineconnector_command += f',comment={comment}'
#     app.logger.debug(f"Sending PineConnector command: {pineconnector_command}")
#     response = requests.post(config.PINECONNECTOR_WEBHOOK_URL, data=pineconnector_command)
#     app.logger.debug(f"PineConnector response: {response.text}")

# if __name__ == "__main__":
#     app.run(host='0.0.0.0', port=5000, debug=True)

