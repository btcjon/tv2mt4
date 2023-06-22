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

def send_to_pineconnector(action, symbol, risk):
    data = f"{config.LICENSE_ID},{action},{symbol},risk={risk}"
    response = requests.post(config.PINECONNECTOR_WEBHOOK_URL, data=data)
    print(f"Sent {action} command for {symbol} to Pineconnector, response: {response.text}")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.data.decode('utf-8')
    app.logger.debug(f"Received webhook data: {data}")
    parts = data.split()
    
    if parts[0] in ["up", "down"]:
        # This is a trend update webhook
        command, symbol, *risk = parts
    else:
        # This is a buy or sell webhook
        command, symbol, *risk = parts

    risk = 0.007  # default risk
    for part in parts:
        if part.startswith("risk="):
            try:
                risk = float(part.split("=")[1])
            except (IndexError, ValueError):
                app.logger.debug(f"Failed to parse risk from part: {part}")


    record = get_matching_record(symbol)
    if record:
        app.logger.debug(f"Found record for {symbol} with state {record['fields']['State']} and trend {record['fields']['Trend']}")
        if command == "buy":
            if record['fields']['Trend'] == "down" and record['fields']['State'] == "closed":
                app.logger.debug(f"Ignoring buy command for {symbol} because trend is down and state is closed")
            else:
                send_to_pineconnector(command, symbol, risk)
                update_airtable_record(record['id'], "open", command)

        elif command == "sell":
            send_to_pineconnector("closelong", symbol, risk)
            update_airtable_record(record['id'], "closed", command)
        elif command in ["up", "down"]:
            update_airtable_trend(symbol, command)
    return '', 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
