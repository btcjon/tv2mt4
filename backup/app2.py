from flask import Flask, request
from airtable import Airtable
from pyngrok import ngrok
import requests
import config
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

airtable = Airtable(config.AIRTABLE_BASE_ID, 'table1', api_key=config.AIRTABLE_API_KEY)

def send_to_pineconnector(action, symbol, risk):
    url = 'https://pineconnector.net/webhook/'
    license_id = '67009604159571'
    if action == 'buy':
        data = f'{license_id},buy,{symbol},risk={risk}'
    else:
        data = f'{license_id},closelong,{symbol}'
    logging.info(f'Sending data to Pineconnector: {data}')
    response = requests.post(url, data=data)
    if response.text:
        logging.info(f'Response from Pineconnector: {response.text}')
    else:
        logging.info('No response from Pineconnector.')
    return response.text

@app.route('/webhook', methods=['POST'])
def webhook():
    message = request.get_data(as_text=True)
    action, symbol = message.split()
    logging.info(f'Received {action} command for {symbol}')
    records = airtable.get_all(formula=f"{{Symbol}} = '{symbol}'")
    if records:
        record = records[0]
        state = record['fields'].get('State')
        trend = record['fields'].get('Trend')
        logging.info(f'Found record for {symbol} with state {state} and trend {trend}')
        if action == 'buy' and state == 'closed' and trend == 'up':
            response = send_to_pineconnector(action, symbol, 0.45)
            airtable.update(record['id'], {'State': 'open', 'Last Command': 'buy'})
        elif action == 'sell':
            response = send_to_pineconnector(action, symbol, 0.45)
            airtable.update(record['id'], {'State': 'closed', 'Last Command': 'sell'})
    return '', 200

if __name__ == '__main__':
    ngrok.set_auth_token(config.NGROK_AUTH_TOKEN)
    public_url = ngrok.connect(80)
    print(f"Ngrok tunnel opened at {public_url}")
    app.run(host='0.0.0.0', port=80)
