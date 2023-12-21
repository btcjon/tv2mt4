from flask import request, current_app as app
import logging
import config
from airtable_operations import AirtableOperations
from utils import parse_webhook_data, handle_update_message, handle_order_message

def webhook():
    try:
        message_dict = parse_webhook_data(request.data)
        message_type = message_dict.get('message_type')
        symbol = message_dict.get('symbol')
        entry = message_dict.get('entry')

        if message_type == 'update':
            return handle_update_message(symbol, message_dict)
        elif message_type == 'order':
            return handle_order_message(symbol, message_dict, entry)

        # Add a default return at the end of the function
        return '', 200
    except Exception as e:
        app.logger.exception(f"An unhandled exception occurred in the webhook function: {e}")
        return 'Error', 500
            order_type = message_dict.get('order-type')
            risk = message_dict.get('risk')
            tp = message_dict.get('tp')
            sl = message_dict.get('sl')
            comment = message_dict.get('comment')
            app.logger.info(f"Processing order message for symbol: {symbol}")

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
                app.logger.info(f"Order Skipped: {symbol} - Time restriction ({start} - {end})")
                app.logger.info(f"Time Restriction filter applied: Current time {now} is within the restricted period from {start} to {end}.")
                return '', 200  # If it is, do not send any commands to PineConnector

            #We need to check config if BB_Filter is set to True
            if getattr(config, 'BB_Filter', False):
                record = airtable_operations.get_matching_record(symbol)
                if record:
                    bb_present = record['fields'].get('BB')  # get the BB field
                    if bb_present:
                        app.logger.info(f"Order not sent due to BB filter for symbol: {symbol}")
                        app.logger.info(f"BB filter applied: Order for {symbol} filtered because BB is present.")
                        return '', 200  # if BB is present, do not send command to PineConnector
            record = airtable_operations.get_matching_record(symbol)
            if record:
                bb_present = record['fields'].get('BB')  # get the BB field
                if bb_present:
                    app.logger.info(f"BB filter applied: Order for {symbol} filtered because BB is present.")
                    return '', 200  # if BB is present, do not send command to PineConnector

            # If entry is false, bypass all filters except for FILTER_TIME and BB_Filter
            if not entry:
                app.logger.info(f"Order Sent: {symbol} - Filters bypassed (entry=false)")
                send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)
                return '', 200

            # Check for closelong and closeshort order types
            if order_type in ['closelong', 'closeshort']:
                # Check for Time Restriction and BB Restriction
                app.logger.info(f"Sending close order to PineConnector for symbol: {symbol}")
                send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)
                airtable_operations.update_airtable_field(symbol, f'State {order_type[5:].capitalize()}', 'closed')
                airtable_operations.reset_airtable_field(symbol, f'{order_type[5:].capitalize()}#')

            # Add the check for Long# and Short# fields being greater than '0'
            if order_type == 'long':
                long_count = int(record['fields'].get('Long#', 0))
                trend = record['fields'].get('Trend')
                resistance = record['fields'].get('Resistance', False)
                td9sell = record['fields'].get('TD9sell', False)
                # Check if Long# is greater than 0 or if trend is up and no resistance or TD9sell signal is present
                if long_count > 0:
                    app.logger.info(f"Long# filter bypassed: Long# for {symbol} is greater than 0.")
                if trend == 'up':
                    app.logger.info(f"Trend filter passed: Trend for {symbol} is up.")
                if resistance:
                    app.logger.info(f"Resistance filter failed: Resistance for {symbol} is present.")
                if td9sell:
                    app.logger.info(f"TD9sell filter failed: TD9sell for {symbol} is present.")
                if long_count > 0 or (trend == 'up' and not resistance and not td9sell):
                    app.logger.info(f"Sending PineConnector command for {symbol} as all filters passed or Long# is greater than 0.")
                    app.logger.info(f"Sending long order to PineConnector for symbol: {symbol}")
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
                if short_count > 0:
                    app.logger.info(f"Short# filter bypassed: Short# for {symbol} is greater than 0.")
                if trend == 'down':
                    app.logger.info(f"Trend filter passed: Trend for {symbol} is down.")
                if support:
                    app.logger.info(f"Support filter failed: Support for {symbol} is present.")
                if td9buy:
                    app.logger.info(f"TD9buy filter failed: TD9buy for {symbol} is present.")
                if short_count > 0 or (trend == 'down' and not support and not td9buy):
                    app.logger.info(f"Sending PineConnector command for {symbol} as all filters passed or Short# is greater than 0.")
                    app.logger.info(f"Sending short order to PineConnector for symbol: {symbol}")
                    send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)
                    if short_count == 0:  # Only update if Short# was 0
                        airtable_operations.update_airtable_field(symbol, 'State Short', 'open')
                        airtable_operations.increment_airtable_field(symbol, 'Short#')
            elif order_type in ['closelong', 'closeshort']:
                app.logger.info(f"Sending close order to PineConnector for symbol: {symbol}")
                send_pineconnector_command(order_type, symbol, risk, tp, sl, comment)
                airtable_operations.update_airtable_field(symbol, f'State {order_type[5:].capitalize()}', 'closed')
                airtable_operations.reset_airtable_field(symbol, f'{order_type[5:].capitalize()}#')

            return '', 200

        # Add a default return at the end of the function
        return '', 200
    except Exception as e:
        app.logger.exception(f"An unhandled exception occurred in the webhook function: {e}")
        app.logger.exception(f"An unhandled exception occurred in the webhook function: {e}")
        return 'Error', 500

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
