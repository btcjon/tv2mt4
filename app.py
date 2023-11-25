from flask import Flask, request
from airtable import Airtable
import requests
import config
import logging
from datetime import datetime, time

app = Flask(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

airtable = Airtable(config.AIRTABLE_BASE_ID, config.AIRTABLE_TABLE_NAME, api_key=config.AIRTABLE_API_KEY)

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


def get_matching_record(symbol):
    symbol_without_pro = symbol.replace('.PRO', '')
    records = airtable.get_all(formula=f"{{Symbol}} = '{symbol_without_pro}'")
    return records[0] if records else None

def update_airtable_trend(symbol, trend):
    record = get_matching_record(symbol)
    app.logger.debug(f"Updating trend for {symbol} to {trend}")
    if record:
        response = airtable.update(record['id'], {'Trend': trend})
        app.logger.debug(f"Airtable update response: {response}")

def update_airtable_snr(symbol, snr):
    record = get_matching_record(symbol)
    app.logger.debug(f"Updating SnR for {symbol} to {snr}")
    if record:
        response = airtable.update(record['id'], {'SnR': snr})
        app.logger.debug(f"Airtable update response: {response}")

def update_airtable_state(symbol, state, command):
    record = get_matching_record(symbol)
    state_field = 'State Long' if command == 'long' else 'State Short'
    app.logger.debug(f"Updating {state_field} for {symbol} to {state}")
    if record:
        response = airtable.update(record['id'], {state_field: state})
        app.logger.debug(f"Airtable update response: {response}")

def update_airtable_count(symbol, command):
    record = get_matching_record(symbol)
    count_field = 'Count Long' if command == 'long' else 'Count Short'
    if record:
        count = record['fields'].get(count_field, '-')
        count = '0' if count == '-' else str(int(count) + 1)
        response = airtable.update(record['id'], {count_field: count})
        app.logger.debug(f"Airtable update response: {response}")

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.data.decode('utf-8')
        app.logger.debug(f"Received webhook data: {data}")
        parts = data.split(',')
        app.logger.debug(f"Parsed webhook parts: {parts}")

        # Rest of the existing code...

    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return 'Error', 500

    message = parts[0]

    if "Zone Found" in message:
        pass
    elif "enters" in message and "Support" in message:
        symbol = message.split(' - ')[0]
        update_airtable_snr(symbol, "Support")
    elif "enters" in message and "Resistance" in message:
        symbol = message.split(' - ')[0]
        update_airtable_snr(symbol, "Resistance")
    elif "is breaking" in message:
        symbol = message.split(' - ')[0]
        update_airtable_snr(symbol, "-")

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

        # Additional logging to verify Airtable update
        app.logger.debug(f"Attempting to update Airtable for symbol: {symbol} with trend: {command}")

        record = get_matching_record(symbol)
        app.logger.debug(f"Retrieved record: {record}")

        if record:
            state_field = 'State Long' if command == 'long' else 'State Short'
            state = record['fields'].get(state_field)
            trend = record['fields'].get('Trend')
            snr = record['fields'].get('SnR')

            app.logger.debug(f"Retrieved state: {state}, trend: {trend}, snr: {snr}")

            if command in ["up", "down", "flat"]:
                update_airtable_trend(symbol, command)
            elif (command == "long" and trend == "up" and snr != "Resistance") or (command == "short" and trend == "down" and snr != "Support"):
                send_pineconnector_command(license_id, command, symbol, risk, tp, sl, comment)
    return '', 200

def send_pineconnector_command(license_id, command, symbol, risk, tp, sl, comment):
    pineconnector_command = generate_pineconnector_command(license_id, command, symbol, risk, tp, sl, comment)
    app.logger.debug(f"Sending PineConnector command: {pineconnector_command}")
    response = requests.post(config.PINECONNECTOR_WEBHOOK_URL, data=pineconnector_command)
    app.logger.debug(f"PineConnector response: {response.text}")
    if response.status_code != 200:
        app.logger.error(f"Failed to send PineConnector command: {response.text}")

    if response.status_code == 200:  # Check the response status code
        update_airtable_state(symbol, "open", command)
        update_airtable_count(symbol, command)
    else:
        app.logger.error(f"Failed to send PineConnector command: {response.text}")

    if response.status_code == 200:  # Check the response status code
        update_airtable_state(symbol, "open", command)
        update_airtable_count(symbol, command)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
