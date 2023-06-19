from flask import Flask, request
from airtable import Airtable
import requests
import config

app = Flask(__name__)
app.debug = True

airtable = Airtable(config.AIRTABLE_BASE_ID, config.AIRTABLE_TABLE_NAME, api_key=config.AIRTABLE_API_KEY)

def get_matching_record(symbol):
    try:
        records = airtable.get_all(formula=f"{{Symbol}} = '{symbol}'")
        return records[0] if records else None
    except Exception as e:
        app.logger.error(f"Error getting record for {symbol}: {e}")
        return None

def update_airtable_record(record_id, state, last_command):
    try:
        airtable.update(record_id, {'State': state, 'Last Command': last_command})
    except Exception as e:
        app.logger.error(f"Error updating record {record_id}: {e}")

def send_to_pineconnector(action, symbol, risk):
    try:
        data = f"{config.LICENSE_ID},{action},{symbol},risk={risk}"
        response = requests.post(config.PINECONNECTOR_WEBHOOK_URL, data=data)
        app.logger.info(f"Sent {action} command for {symbol} to Pineconnector, response: {response.text}")
    except Exception as e:
        app.logger.error(f"Error sending {action} command for {symbol} to Pineconnector: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.data.decode('utf-8')
    command, symbol, *risk = data.split()
    risk = risk[0] if risk else "0.45"
    app.logger.info(f"Received {command} command for {symbol} with risk {risk}")
    record = get_matching_record(symbol)
    if record:
        app.logger.info(f"Found record for {symbol} with state {record['fields']['State']} and trend {record['fields']['Trend']}")
        if command == "buy" and (record['fields']['State'] != "closed" or record['fields']['Trend'] != "down"):
            send_to_pineconnector(command, symbol, risk)
            update_airtable_record(record['id'], "open", command)
        elif command == "sell":
            send_to_pineconnector("closelong", symbol, risk)
            update_airtable_record(record['id'], "closed", command)
    return '', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
