from flask import Flask, request
from message_parser import MessageParser
from command_handlers import UpdateSnRHandler, UpdateTrendHandler
import logging

app = Flask(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

# Instantiate command handlers
update_snr_handler = UpdateSnRHandler()
update_trend_handler = UpdateTrendHandler()

# Update the message_handlers dictionary to use the new command handler instances
message_handlers = {
    "enters Support": update_snr_handler.handle,
    "enters Resistance": update_snr_handler.handle,
    "is breaking": update_snr_handler.handle,
    "up": update_trend_handler.handle,
    "down": update_trend_handler.handle,
    "flat": update_trend_handler.handle,
    # ... other handlers will be updated similarly ...
}

@app.route('/webhook', methods=['POST'])
def webhook():
    message_parser = MessageParser()
    try:
        data = request.data.decode('utf-8')
        app.logger.debug(f"Received webhook data: {data}")
        message = message_parser.parse(data)

        if message:
            handler = message_handlers.get(message.command)
            if handler:
                handler(message)
            else:
                app.logger.error(f"No handler found for command: {message.command}")
        else:
            app.logger.error("Failed to parse message")

        return '', 200

    except Exception as e:
        app.logger.error(f"An error occurred: {e}")
        return 'Error', 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
