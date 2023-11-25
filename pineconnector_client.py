import requests
import config

class PineConnectorClient:
    @staticmethod
    def generate_command(license_id, command, symbol, risk=None, tp=None, sl=None, comment=None):
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

    @staticmethod
    def send_command(license_id, command, symbol, risk, tp, sl, comment, logger):
        pineconnector_command = PineConnectorClient.generate_command(license_id, command, symbol, risk, tp, sl, comment)
        logger.debug(f"Sending PineConnector command: {pineconnector_command}")
        response = requests.post(config.PINECONNECTOR_WEBHOOK_URL, data=pineconnector_command)
        logger.debug(f"PineConnector response: {response.text}")
        return response
