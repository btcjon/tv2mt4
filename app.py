# app.py
from flask import Flask, request
import logging
from airtable_operations import AirtableOperations
import requests
import config

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

message_handlers = {
    "Zone Found": handle_zone_found,
    "enters Support": handle_enters_support,
    "enters Resistance": handle_enters_resistance,
    "is breaking": handle_is_breaking,
    # add more as needed
}

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.data.decode('utf-8')
        app.logger.debug(f"Received webhook data: {data}")
        parts = data.split(',')
        app.logger.debug(f"Parsed webhook parts: {parts}")

        message = parts[0]

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