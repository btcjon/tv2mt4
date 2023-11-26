# app.py
from flask import Flask, request
import logging
from airtable_operations import AirtableOperations
import config
from datetime import datetime, time

app = Flask(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

airtable_operations = AirtableOperations()


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

from command_handlers import UpdateSnRHandler, UpdateTrendHandler

# Instantiate command handlers
update_snr_handler = UpdateSnRHandler(airtable_operations)
update_trend_handler = UpdateTrendHandler(airtable_operations)

# Update the message_handlers dictionary to use the new command handler instances
message_handlers = {
    "enters Support": update_snr_handler.handle,
    "enters Resistance": update_snr_handler.handle,
    "is breaking": update_snr_handler.handle,
    "up": update_trend_handler.handle,
    "down": update_trend_handler.handle,
    "flat": update_trend_handler.handle,
    # ... other handlers will be updated similarly ...
}

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

# The duplicated logic for handling PineConnector commands will be consolidated into the handle_pineconnector_command function.
# The unnecessary code block within the webhook function will be removed.

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
