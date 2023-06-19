from flask import Flask, request
from airtable import Airtable
import requests
import config

app = Flask(__name__)

airtable = Airtable(config.AIRTABLE_BASE_ID, config.AIRTABLE_TABLE_NAME, api_key=config.AIRTABLE_API_KEY)

def get_matching_record(symbol):
    records = airtable.get_all(formula=f"{{Symbol}} = '{symbol}'")
    return records[0] if records else None

def update_airtable_record(record_id, state, last_command):
    airtable.update(record_id, {'State': state, 'Last Command': last_command})

def send_to_pineconnector(action, symbol, risk):
    data = f"{config.LICENSE_ID},{action},{symbol},risk={risk}"
    response = requests.post(config.PINECONNECTOR_WEBHOOK_URL, data=data)
    print(f"Sent {action} command for {symbol} to Pineconnector, response: {response.text}")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.data.decode('utf-8')
    parts = data.split()
    if len(parts) == 2 and parts[1] in ["up", "down"]:  # This is a trend update
        symbol, trend = parts
        record = get_matching_record(symbol)
        if record:
            print(f"Updating trend for {symbol} to {trend}")
            airtable.update(record['id'], {'Trend': trend})
    else:  # This is a buy/sell command
        command, symbol, *risk = parts
        risk = float(risk[0].split('=')[1]) if risk else 0.45
        print(f"Received {command} command for {symbol} with risk {risk}")
        record = get_matching_record(symbol)
        if record:
            print(f"Found record for {symbol} with state {record['fields']['State']} and trend {record['fields']['Trend']}")
            if command == "buy" and (record['fields']['State'] != "closed" or record['fields']['Trend'] != "down"):
                send_to_pineconnector(command, symbol, risk)
                update_airtable_record(record['id'], "open", command)
            elif command == "sell":
                send_to_pineconnector("closelong", symbol, risk)
                update_airtable_record(record['id'], "closed", command)
    return '', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
