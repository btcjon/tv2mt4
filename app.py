from flask import Flask, request
import logging
from datetime import datetime, time
from message_parser import MessageParser
from airtable_manager import AirtableManager
from pineconnector_client import PineConnectorClient
import config

app = Flask(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

message_parser = MessageParser()
airtable_manager = AirtableManager()
pineconnector_client = PineConnectorClient()

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
    alert_details = message_parser.parse_alert(data)
    symbol = alert_details.get("symbol")

    if alert_details.get("is_zone_found"):
        pass  # Handle zone found case if needed
    elif alert_details.get("enters_support"):
        airtable_manager.update_snr(symbol, "Support", app.logger)
    elif alert_details.get("enters_resistance"):
        airtable_manager.update_snr(symbol, "Resistance", app.logger)
    elif alert_details.get("is_breaking"):
        airtable_manager.update_snr(symbol, "-", app.logger)

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

        record = airtable_manager.get_matching_record(symbol)
        app.logger.debug(f"Retrieved record: {record}")

        if record:
            state_field = 'State Long' if command == 'long' else 'State Short'
            state = record['fields'].get(state_field)
            trend = record['fields'].get('Trend')
            snr = record['fields'].get('SnR')

            app.logger.debug(f"Retrieved state: {state}, trend: {trend}, snr: {snr}")

            if command in ["up", "down", "flat"]:
                airtable_manager.update_trend(symbol, command, app.logger)
            elif (command == "long" and trend == "up" and snr != "Resistance") or (command == "short" and trend == "down" and snr != "Support"):
                response = pineconnector_client.send_command(license_id, command, symbol, risk, tp, sl, comment, app.logger)
                if response.status_code == 200:
                    airtable_manager.update_state(symbol, "open", command, app.logger)
                    airtable_manager.update_count(symbol, command, app.logger)
    return '', 200

# This function is removed because it is now handled by the PineConnectorClient class.

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
