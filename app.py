
from flask import Flask
from logger import setup_logger
from webhook_handlers import webhook

app = Flask(__name__)
app.logger = setup_logger()

@app.route('/webhook', methods=['POST'])
def webhook_route():
    return webhook()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
