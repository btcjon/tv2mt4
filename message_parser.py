class MessageParser:
    @staticmethod
    def parse_alert(alert):
        alert_details = {"is_bearish": False, "symbol": None}
        parts = alert.split(" ")

        if parts[0].lower() == "bearish":
            alert_details["is_bearish"] = True
            alert_details["symbol"] = parts[-1]

        return alert_details
