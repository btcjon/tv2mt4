from flask import Flask, request
from airtable_manager import AirtableManager
from message_parser import MessageParser
from airtable_manager import AirtableManager
from pineconnector_client import PineConnectorClient
from pineconnector_client import PineConnectorClient
import logging
from datetime import datetime, time

app = Flask(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

airtable = Airtable(config.AIRTABLE_BASE_ID, config.AIRTABLE_TABLE_NAME, api_key=config.AIRTABLE_API_KEY)

# This function is removed because it is now handled by the MessageParser class.

# This function is removed because it is now handled by the PineConnectorClient class.


# This function is removed because it is now handled by the AirtableManager class.

# This function is removed because it is now handled by the AirtableManager class.

# This function is removed because it is now handled by the AirtableManager class.

# This function is removed because it is now handled by the AirtableManager class.

# This function is removed because it is now handled by the AirtableManager class.

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.data.decode('utf-8')
    app.logger.debug(f"Received webhook data: {data}")
    parts = data.split(',')

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
        else:
            license_id = parts[0]
            command = parts[1]
            symbol = parts[2]
            risk = parts[3] if len(parts) > 3 else None
            tp = None  # tp is not provided in the webhook data
            sl = None  # sl is not provided in the webhook data
            comment = parts[4].split('=')[1].strip('\"') if len(parts) > 4 else None
            app.logger.debug(f"Parsed command: {command}, symbol: {symbol}, risk: {risk}, tp: {tp}, sl: {sl}, comment: {comment}")

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
