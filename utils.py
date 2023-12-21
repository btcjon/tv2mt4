
import requests
import config
import logging

def send_pineconnector_command(order_type, symbol, risk, tp, sl, comment):
    if not symbol.endswith('.PRO') and symbol != 'USTEC100':
        symbol += '.PRO'  # append '.PRO' to the symbol only if it's not already there
    pineconnector_command = f"{config.PINECONNECTOR_LICENSE_ID},{order_type},{symbol}"
    if risk:
        pineconnector_command += f",risk={risk}"
    if tp:
        pineconnector_command += f",tp={tp}"
    if sl:
        pineconnector_command += f",sl={sl}"
    if comment:
        # Ensure the comment is included with only a single set of quotes
        pineconnector_command += f',comment={comment}'
    response = requests.post(config.PINECONNECTOR_WEBHOOK_URL, data=pineconnector_command)
    app.logger.debug(f"PineConnector response: {response.status_code} {response.reason} - {response.text}")
