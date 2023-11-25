Refactored Application Overview
-------------------------------

The refactored Flask application is designed to handle incoming webhook data, parse the content, and perform various actions based on the parsed data. The application is modularized into separate components to handle specific functionalities, which makes the codebase more maintainable and scalable.

Components:
- `app.py`: The main Flask application file that defines the webhook endpoint and uses other modules for processing.
- `message_parser.py`: Contains the `MessageParser` class responsible for parsing incoming messages and extracting relevant details.
- `airtable_manager.py`: Contains the `AirtableManager` class that handles all interactions with the Airtable API, such as retrieving records and updating fields.
- `pineconnector_client.py`: Contains the `PineConnectorClient` class for sending commands to the PineConnector service based on the parsed messages.

Webhook Handling Logic:
1. The Flask application starts and listens for POST requests on the `/webhook` endpoint.
2. When a POST request is received, `app.py` reads the incoming data and passes it to the `MessageParser` class.
3. `MessageParser` parses the data and extracts relevant details such as symbols, commands, and any additional parameters.
4. Based on the parsed data, `app.py` may call methods from `AirtableManager` to update records in Airtable. This includes updating trends, support and resistance levels, state, and count fields.
5. If the message indicates a trading command (e.g., "long" or "short"), `app.py` uses `PineConnectorClient` to send the command to the PineConnector service.
6. The application logs the actions taken and any responses from external services for debugging and monitoring purposes.

Message Parsing and Handling:
- The application can handle various message formats and types. The parsing logic is encapsulated within the `MessageParser` class.
- For example, if a message contains the word "bearish," the parser marks the message as bearish and extracts the symbol to be used in further processing.
- The application is designed to be flexible and can be easily extended to handle additional message types and formats by updating the `MessageParser` class.

By separating concerns into different modules, the application becomes easier to manage and update. Each module can be modified independently, allowing for targeted updates and testing without affecting other parts of the application.

1. Updating the 'SnR' field:
   The application updates the 'SnR' (Support and Resistance) field in Airtable based on specific keywords found in the incoming webhook messages. When a message contains phrases like "enters Support" or "enters Resistance," the application identifies the symbol from the message and updates the corresponding 'SnR' field in Airtable to "Support" or "Resistance," respectively. If a message indicates that a symbol "is breaking," the 'SnR' field is cleared.

2. Updating the 'Trend' field:
   The 'Trend' field in Airtable is updated when the incoming webhook message contains a command such as "up," "down," or "flat." The application parses the message, extracts the symbol and the trend direction, and updates the 'Trend' field in Airtable with the new value. This allows the system to track the current trend direction for each symbol.

3. Sending a PineConnector command:
   When the application receives a webhook message with a trading command ("long" or "short"), it constructs a command string to be sent to PineConnector. The command includes the license ID, the action to be taken (long or short), the symbol, and any additional parameters such as risk, take profit (tp), stop loss (sl), and a comment. This command is then sent to the PineConnector webhook URL. If the PineConnector service successfully processes the command, the application proceeds to update the Airtable with the new state and count.

4. Updating of 'State Long' and 'State Short':
   After sending a command to PineConnector, the application updates the 'State Long' or 'State Short' field in Airtable, depending on whether the command was to go long or short. This field represents the current state of the trade for the symbol. Additionally, the application increments the 'Count Long' or 'Count Short' field, which keeps track of the number of times a long or short command has been issued for the symbol.

