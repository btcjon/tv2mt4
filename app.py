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

def generate_pineconnector_command(license_id, command, symbol, risk=None, tp=None, sl=None, comment=None):
    pineconnector_command = f"{license_id},{command},{symbol}"
    if risk:
        pineconnector_command += f",{risk}"
    if tp:
        pineconnector_command += f",{tp}"
    if sl:
        pineconnector_command += f",{sl}"
    if comment:
        pineconnector_command += f",{comment}"
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
    parts = data.split(',')

    license_id = parts[0]
    command = parts[1]
    symbol = parts[2]
    risk = parts[3] if len(parts) > 3 else None
    tp = parts[4] if len(parts) > 4 else None
    sl = parts[5] if len(parts) > 5 else None
    comment = parts[6] if len(parts) > 6 else None

    record = get_matching_record(symbol)
    if record:
        app.logger.debug(f"Found record for {symbol} with state {record['fields']['State']} and trend {record['fields']['Trend']}")
        if command in ["up", "down", "flat"]:
            update_airtable_trend(symbol, command)
        elif (command == "long" and record['fields']['Trend'] == "up") or (command == "short" and record['fields']['Trend'] == "down"):
            if config.CHECK_STATE:
                if record['fields']['State'] == "closed":
                    send_pineconnector_command(license_id, command, symbol, risk, tp, sl, comment, record)
            else:
                send_pineconnector_command(license_id, command, symbol, risk, tp, sl, comment, record)
    return '', 200

def send_pineconnector_command(license_id, command, symbol, risk, tp, sl, comment, record):
    pineconnector_command = generate_pineconnector_command(license_id, command, symbol, risk, tp, sl, comment)
    response = requests.post(config.PINECONNECTOR_WEBHOOK_URL, data=pineconnector_command)
    print(f"Sent command to Pineconnector, response: {response.text}")
    update_airtable_record(record['id'], "open" if command == "long" else "closed", command)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)