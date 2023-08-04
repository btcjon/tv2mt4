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

def generate_pineconnector_command(symbol):
    license_id = "6700960415957"
    command = "bearish"
    risk = "risk=0.0005"
    tp = "tp=0.05"
    sl = "sl=0.05"

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

def update_airtable_count(record_id, command):
    record = airtable.get(record_id)
    count = record['fields'].get('Count', '-')
    app.logger.debug(f"Current count for record {record_id}: {count}")
    if command == 'sell':
        new_count = '-'
    elif command == 'buy':
        if count == '-':
            new_count = '0'
        else:
            new_count = str(int(count) + 1)
    else:
        return
    app.logger.debug(f"Updating count for record {record_id} to {new_count}")
    response = airtable.update(record_id, {'Count': new_count})
    app.logger.debug(f"Airtable update response: {response}")

def send_to_pineconnector(action, symbol, risk):
    data = f"{config.LICENSE_ID},{action},{symbol},risk={risk}"
    response = requests.post(config.PINECONNECTOR_WEBHOOK_URL, data=data)
    print(f"Sent {action} command for {symbol} to Pineconnector, response: {response.text}")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.data.decode('utf-8')
    app.logger.debug(f"Received webhook data: {data}")

    alert_details = parse_alert(data)
    if alert_details["is_bearish"]:
        pineconnector_command = generate_pineconnector_command(alert_details["symbol"])
        response = requests.post(config.PINECONNECTOR_WEBHOOK_URL, data=pineconnector_command)
        print(f"Sent command to Pineconnector, response: {response.text}")
    else:
        parts = data.split()
        command, symbol, *risk = parts
        # Rest of the existing logic...

    return '', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
