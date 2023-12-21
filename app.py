from flask import Flask
from logger import setup_logger
from webhook_handlers import webhook

app = Flask(__name__)
logger = setup_logger()

# ... remove the logging setup code ...

# ... remove the AirtableOperations class and its methods ...

# ... remove the webhook function ...

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

app = Flask(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)  # Set to INFO to reduce the verbosity of the logs
formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)  # Set to INFO to reduce the verbosity of the logs
app.logger.propagate = False

class AirtableOperations:
    def __init__(self):
        self.airtable = Airtable(config.AIRTABLE_BASE_ID, config.AIRTABLE_TABLE_NAME, api_key=config.AIRTABLE_API_KEY)
        self.logger = logging.getLogger(__name__)
        self.logger.propagate = False

    def get_matching_record(self, symbol):
        symbol_without_pro = symbol.replace('.PRO', '')
        records = self.airtable.get_all(formula=f"{{Symbol}} = '{symbol_without_pro}'")
        return records[0] if records else None

    def update_airtable_field(self, symbol, field, value):
        try:
            record = self.get_matching_record(symbol)
            action = 'update' if value not in [False, None] else 'clear'
            if record:
                self.airtable.update(record['id'], {field: value})
                self.logger.info(f"{field} for {symbol} {action}d to {value}")
            else:
                self.logger.error(f"Record not found for {symbol}")
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error on {action} {field} for {symbol}: {e}, retrying...")
            time.sleep(5)  # Wait for 5 seconds before retrying
            try:
                response = self.airtable.update(record['id'], {field: value})
                self.logger.info(f"{field} for {symbol} {action}d to {value} on retry")
            except Exception as retry_e:
                self.logger.error(f"Retry failed for {action} {field} for {symbol}: {retry_e}")
        except Exception as e:
            self.logger.error(f"{action.capitalize()} {field} for {symbol} failed: {e}")

    def increment_airtable_field(self, symbol, field):
        try:
            record = self.get_matching_record(symbol)
            if record:
                count = record['fields'].get(field, 0)  # Ensure the default value is an integer 0
                count = int(count) + 1
                try:
                    self.airtable.update(record['id'], {field: count})  # Send an integer value
                    self.logger.info(f"Incremented {field} for {symbol} by 1")
                except requests.exceptions.HTTPError as http_err:
                    self.logger.error(f"HTTP error on increment {field} for {symbol}: {http_err.response.text}")
                except Exception as e:
                    self.logger.error(f"Increment {field} for {symbol} failed: {e}")
            else:
                self.logger.error(f"Record not found for {symbol}")
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error on increment {field} for {symbol}: {http_err}")
        except Exception as e:
            self.logger.error(f"Increment {field} for {symbol} failed: {e}")

    def reset_airtable_field(self, symbol, field):
        try:
            record = self.get_matching_record(symbol)
            if record:
                self.airtable.update(record['id'], {field: 0})  # Send an integer value for the reset
                self.logger.info(f"Reset {field} for {symbol} to 0")
            else:
                self.logger.error(f"Record not found for {symbol}")
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(f"HTTP error on reset {field} for {symbol}: {http_err}")
        except Exception as e:
            self.logger.error(f"Reset {field} for {symbol} failed: {e}")

airtable_operations = AirtableOperations()

@app.route('/webhook', methods=['POST'])
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
            elif keyword == 'TD9sellOFF':
                field_name = 'TD9sell'
                update_value = False
            elif keyword == 'up':
                field_name = 'Trend'
                update_value = 'up'
            elif keyword == 'down':
                field_name = 'Trend'
                update_value = 'down'
            app.logger.info(f"Update: {symbol} - {keyword} received")
            try:
                if field_name is not None and update_value is not None:
                    airtable_operations.update_airtable_field(symbol, field_name, update_value)  # Log inside method
                else:
                    app.logger.error(f"Unrecognized keyword '{keyword}' for {symbol}")
                return '', 200
            except Exception as e:
                app.logger.exception(f"Airtable update error for {symbol}", exc_info=e)
                return 'Error', 500
        elif message_type == 'order':
            # ... rest of the webhook function ...
            order_type = message_dict.get('order-type')
            risk = message_dict.get('risk')
            tp = message_dict.get('tp')
            sl = message_dict.get('sl')
            comment = message_dict.get('comment')
            # Removed redundant log for processing order message

            # Get the current server time
            now = datetime.utcnow().time()

            # Define the start and end of the restricted period in UTC ( FILTER_TIME = True)
            start = time(21, 55)  # 9:55 PM UTC if not set in config
            end = time(23, 0)  # 11:00 PM UTC if not set in config
            if hasattr(config, 'FILTER_TIME_START'):
                start = config.FILTER_TIME_START
            if hasattr(config, 'FILTER_TIME_END'):
                end = config.FILTER_TIME_END

            # Check if the current time is within the restricted period
            if start <= now <= end:
                app.logger.info(f"Order for {symbol} skipped due to time restriction ({start.strftime('%H:%M')} - {end.strftime('%H:%M')})")
                return '', 200  # If it is, do not send any commands to PineConnector

            #We need to check config if BB_Filter is set to True
            if getattr(config, 'BB_Filter', False):
                record = airtable_operations.get_matching_record(symbol)
                if record:
                    bb_present = record['fields'].get('BB')  # get the BB field
                    if bb_present:
                        app.logger.info(f"Order for {symbol} not sent due to BB filter.")
                        return '', 200  # if BB is present, do not send command to PineConnector
            record = airtable_operations.get_matching_record(symbol)
            if record:
                bb_present = record['fields'].get('BB')  # get the BB field
                if bb_present:
                    # Combined the two log messages into one
                    return '', 200  # if BB is present, do not send command to PineConnector

            # ... rest of the order handling logic ...

            # If entry is false, bypass all filters except for FILTER_TIME and BB_Filter
            if not entry:
                app.logger.info(f"Order for {symbol} sent with filters bypassed (entry=false)")
                send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)
                return '', 200

            # Check for closelong and closeshort order types
            if order_type in ['closelong', 'closeshort']:
                # Check for Time Restriction and BB Restriction
                app.logger.info(f"Close order for {symbol} sent to PineConnector.")
                send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)
                airtable_operations.update_airtable_field(symbol, f'State {order_type[5:].capitalize()}', 'closed')
                airtable_operations.reset_airtable_field(symbol, f'{order_type[5:].capitalize()}#')
            # ... rest of the long and short order handling logic ...
            else:
                # Initialize a list to keep track of which filters passed or failed
                filters_passed = []
                filters_failed = []

                # Check each filter and append the result to the corresponding list
                if order_type == 'long':
                    if long_count > 0:
                        filters_passed.append('Long# > 0')
                    else:
                        filters_failed.append('Long# <= 0')
                    if trend == 'up':
                        filters_passed.append('Trend is up')
                    else:
                        filters_failed.append('Trend is not up')
                    if not resistance:
                        filters_passed.append('No resistance')
                    else:
                        filters_failed.append('Resistance present')
                    if not td9sell:
                        filters_passed.append('No TD9sell')
                    else:
                        filters_failed.append('TD9sell present')

                    if order_type == 'short':
                        if short_count > 0:
                            filters_passed.append('Short# > 0')
                        else:
                            filters_failed.append('Short# <= 0')
                        if trend == 'down':
                            filters_passed.append('Trend is down')
                        else:
                            filters_failed.append('Trend is not down')
                        if not support:
                            filters_passed.append('No support')
                        else:
                            filters_failed.append('Support present')
                        if not td9buy:
                            filters_passed.append('No TD9buy')
                        else:
                            filters_failed.append('TD9buy present')

                        # Log the results of the filter checks
                        if filters_passed:
                            app.logger.info(f"Order for {symbol} passed filters: {', '.join(filters_passed)}")
                        if filters_failed:
                            app.logger.info(f"Order for {symbol} did not pass filters: {', '.join(filters_failed)}")

                        # If any filters failed, do not send the order to PineConnector
                        if filters_failed:
                            return '', 200

                        # If all filters passed, send the order to PineConnector
                        app.logger.info(f"Sending order to PineConnector for symbol: {symbol}")
                        send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)

                        # Update Airtable fields if necessary
                        if order_type == 'long' and long_count == 0:
                            airtable_operations.update_airtable_field(symbol, 'State Long', 'open')
                            airtable_operations.increment_airtable_field(symbol, 'Long#')
                        elif order_type == 'short' and short_count == 0:
                            airtable_operations.update_airtable_field(symbol, 'State Short', 'open')
                            airtable_operations.increment_airtable_field(symbol, 'Short#')

                    return '', 200

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
                # Ensure the comment is included with only a single set of quotes
                pineconnector_command += f',comment={comment}'
            response = requests.post(config.PINECONNECTOR_WEBHOOK_URL, data=pineconnector_command)
            app.logger.debug(f"PineConnector response: {response.status_code} {response.reason} - {response.text}")

        if __name__ == "__main__":
            app.run(host='0.0.0.0', port=5000, debug=True)
