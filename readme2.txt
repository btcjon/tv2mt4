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
