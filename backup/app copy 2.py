from flask import Flask, request
from airtable import Airtable
import requests
import config
import logging

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

def generate_pineconnector_command(command, symbol):
    license_id = "6700960415957"
    risk = "risk=0.01"
    tp = "tp=0.1"
    sl = "sl=0.1"
    comment = 'comment="L1"'

    pineconnector_command = f"{license_id},{command},{symbol},{risk},{tp},{sl},{comment}"
    
    return pineconnector_command

    pineconnector_command = f"{license_id},{command},{symbol},{risk},{tp},{sl}"
    
    return pineconnector_command

def get_matching_record(symbol):
    records = airtable.get_all(formula=f"{{Symbol}} = '{symbol}'")
    return records[0] if records else None

def update_airtable_record(record_id, state, last_command):
    airtable.update(record_id, {'State': state, 'Last Command': last_command})

def update_airtable_trend(symbol, trend):
    record = get_matching_record(symbol)
    app.logger.debug(f"Updating trend for {symbol} to {trend}")
    if record:
        response = airtable.update(record['id'], {'Trend': trend})
        app.logger.debug(f"Airtable update response: {response}")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.data.decode('utf-8')
    app.logger.debug(f"Received webhook data: {data}")
    parts = data.split()
    
    command, symbol, *risk_parts = parts
    risk = 0.002  # default risk
    for part in risk_parts:
        if part.startswith("risk="):
            try:
                risk = float(part.split("=")[1])
            except (IndexError, ValueError):
                app.logger.debug(f"Failed to parse risk from part: {part}")

    record = get_matching_record(symbol)
    if record:
        app.logger.debug(f"Found record for {symbol} with state {record['fields']['State']} and trend {record['fields']['Trend']}")
        if command in ["up", "down", "flat"]:
            update_airtable_trend(symbol, command)
        elif record['fields']['Trend'] != "flat":
            if command == "long" and record['fields']['Trend'] == "up":
                pineconnector_command = generate_pineconnector_command(command, symbol)
                response = requests.post(config.PINECONNECTOR_WEBHOOK_URL, data=pineconnector_command)
                print(f"Sent command to Pineconnector, response: {response.text}")
                update_airtable_record(record['id'], "open", command)
            elif command == "short" and record['fields']['Trend'] == "down":
                pineconnector_command = generate_pineconnector_command(command, symbol)
                response = requests.post(config.PINECONNECTOR_WEBHOOK_URL, data=pineconnector_command)
                print(f"Sent command to Pineconnector, response: {response.text}")
                update_airtable_record(record['id'], "closed", command)
    return '', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)