# app.py
from flask import Flask, request
import logging
from airtable_operations import AirtableOperations
import requests
import config
from datetime import datetime, time

app = Flask(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

airtable_operations = AirtableOperations()

def parse_alert(alert):
    alert_details = {"is_bearish": False, "symbol": None}
    parts = alert.split(" ")

    if parts[0].lower() == "bearish":
        alert_details["is_bearish"] = True
        alert_details["symbol"] = parts[-1]

    return alert_details

def generate_pineconnector_command(license_id, command, symbol, risk=None, tp=None, sl=None, comment=None):
    pineconnector_command = f"{license_id},{command},{symbol}"
    if risk:
        pineconnector_command += f",{risk}"
    if tp:
        pineconnector_command += f",tp={tp}"
    if sl:
        pineconnector_command += f",sl={sl}"
    if comment:
        pineconnector_command += f",comment=\"{comment}\""
    return pineconnector_command.replace(",tp=None", "").replace(",sl=None", "")


# define how to parse the messages
def handle_zone_found(message):
    pass  # No action is taken for "Zone Found" scenario

def handle_enters_support(message):
    symbol = message.split(' - ')[0]
    airtable_operations.update_airtable_snr(symbol, "Support")

def handle_enters_resistance(message):
    symbol = message.split(' - ')[0]
    airtable_operations.update_airtable_snr(symbol, "Resistance")

def handle_is_breaking(message):
    symbol = message.split(' - ')[0]
    airtable_operations.update_airtable_snr(symbol, "-")

def handle_trend(message):
    parts = message.split(',')
    if len(parts) != 3:
        app.logger.error(f"Invalid trend update command: {message}")
        return

    license_id, trend, symbol = parts
    airtable_operations.update_airtable_trend(symbol, trend)

def handle_td9buy(message):
    parts = message.split(' ')
    if len(parts) < 3:
        app.logger.error(f"Invalid TD9buy command: {message}")
        return

    if parts[1] == "OFF":
        command, symbol = parts[2], parts[3]
    else:
        command, symbol = parts[1], parts[2]
    airtable_operations.update_airtable_td9buy(symbol, command != "OFF")

def handle_td9sell(message):
    parts = message.split(' ')
    if len(parts) < 3:
        app.logger.error(f"Invalid TD9sell command: {message}")
        return

    if parts[1] == "OFF":
        command, symbol = parts[2], parts[3]
    else:
        command, symbol = parts[1], parts[2]
    airtable_operations.update_airtable_td9sell(symbol, command != "OFF")

def handle_pineconnector_command(message):
    parts = message.split(',')
    if len(parts) < 3:
        app.logger.error(f"Invalid PineConnector command: {message}")
        return

    license_id, command, symbol = parts[:3]
    risk = tp = sl = comment = None
    for part in parts[3:]:
        if part.startswith('risk='):
            risk = part.split('=')[1]
        elif part.startswith('tp='):
            tp = part.split('=')[1]
        elif part.startswith('sl='):
            sl = part.split('=')[1]
        elif part.startswith('comment='):
            comment = part.split('=')[1]

    # Get the current server time
    now = datetime.utcnow().time()

    # Define the start and end of the restricted period in UTC
    start = time(21, 55)  # 9:55 PM UTC
    end = time(23, 0)  # 11:00 PM UTC

    # Check if the current time is within the restricted period
    if start <= now <= end:
        return  # If it is, do not send any commands to PineConnector

    if command in ['closelong', 'closeshort']:
        send_pineconnector_command(license_id, command, symbol, risk, tp, sl, comment)
    else:
        record = airtable_operations.get_matching_record(symbol)
        if record:
            bb_present = record['fields'].get('BB')  # get the BB field
            if bb_present:
                return  # if BB is present, do not send command to PineConnector

            state_field = 'State Long' if command == 'long' else 'State Short'
            state = record['fields'].get(state_field)
            trend = record['fields'].get('Trend')
            snr = record['fields'].get('SnR')

            if (command == "long" and trend == "up" and snr != "Resistance") or (command == "short" and trend == "down" and snr != "Support"):
                send_pineconnector_command(license_id, command, symbol, risk, tp, sl, comment)

message_handlers = {
    "Zone Found": handle_zone_found,
    "enters Support": handle_enters_support,
    "enters Resistance": handle_enters_resistance,
    "is breaking": handle_is_breaking,
    "up": handle_trend,
    "down": handle_trend,
    "flat": handle_trend, 
    "long": handle_pineconnector_command,
    "short": handle_pineconnector_command,
    "closelong": handle_pineconnector_command,
    "closeshort": handle_pineconnector_command,
    "1H TD9buy": handle_td9buy,
    "1H TD9sell": handle_td9sell,
    # add more as needed
}

from message import Message
from message_parser import MessageParser

@app.route('/webhook', methods=['POST'])
def webhook():
    message_parser = MessageParser()
    try:
        data = request.data.decode('utf-8')
        app.logger.debug(f"Received webhook data: {data}")
        message = message_parser.parse(data)

        for keyword, handler in message_handlers.items():
            if keyword in message:
                handler(message)
                break

        if len(parts) >= 2:
            license_id = risk = tp = sl = comment = None
            if len(parts) == 2:
                command, symbol = parts
                app.logger.debug(f"Received trend update command: {command} for symbol: {symbol}")
            else:
                license_id = parts[0]
                command = parts[1]
                symbol = parts[2]
                risk = parts[3] if len(parts) > 3 else None
                tp = None  # tp is not provided in the webhook data
                sl = None  # sl is not provided in the webhook data
                comment = parts[4].split('=')[1].strip('\"') if len(parts) > 4 else None
                app.logger.debug(f"Parsed command: {command}, symbol: {symbol}, risk: {risk}, tp: {tp}, sl: {sl}, comment: {comment}")

            app.logger.debug(f"Attempting to update Airtable for symbol: {symbol} with trend: {command}")

            record = airtable_operations.get_matching_record(symbol)
            app.logger.debug(f"Retrieved record: {record}")

            if record:
                state_field = 'State Long' if command == 'long' else 'State Short'
                state = record['fields'].get(state_field)
                trend = record['fields'].get('Trend')
                snr = record['fields'].get('SnR')

                app.logger.debug(f"Retrieved state: {state}, trend: {trend}, snr: {snr}")

                if command in ["up", "down", "flat"]:
                    airtable_operations.update_airtable_trend(symbol, command)
                elif (command == "long" and trend == "up" and snr != "Resistance") or (command == "short" and trend == "down" and snr != "Support"):
                    send_pineconnector_command(license_id, command, symbol, risk, tp, sl, comment)
        return '', 200

    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return 'Error', 500

def send_pineconnector_command(license_id, command, symbol, risk, tp, sl, comment):
    pineconnector_command = generate_pineconnector_command(license_id, command, symbol, risk, tp, sl, comment)
    app.logger.debug(f"Sending PineConnector command: {pineconnector_command}")
    response = requests.post(config.PINECONNECTOR_WEBHOOK_URL, data=pineconnector_command)
    app.logger.debug(f"PineConnector response: {response.text}")

    if response.status_code == 200:
        airtable_operations.update_airtable_state(symbol, "In Progress", command)
        airtable_operations.update_airtable_count(symbol, command)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
