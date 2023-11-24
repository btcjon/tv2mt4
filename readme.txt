1. Updating the 'SnR' field: When a webhook is received with a message indicating a price movement for a symbol, the 'SnR' field for that symbol is updated in Airtable. The specific rules are:
- If the price enters the Support Zone (regardless of the timeframe), 'SnR' is set to "Support".
- If the price enters the Resistance Zone (regardless of the timeframe), 'SnR' is set to "Resistance".
- If the price is breaking out or down the Support Zone (regardless of the timeframe), 'SnR' is set to "-".

2. Updating the 'Trend' field: When a webhook is received with a command indicating the trend for a symbol, the 'Trend' field for that symbol is updated in Airtable. The specific rules are:
- If the command is "up", 'Trend' is set to "up".
- If the command is "down", 'Trend' is set to "down".
- If the command is "flat", 'Trend' is set to "flat".

3. Updating the 'State' and 'Count' fields: The 'State Long', 'State Short', 'Count Long', and 'Count Short' fields are updated based on the received command. The specific rules are:
- If the command is "closelong" or "closeshort", the corresponding 'State' field is set to "closed" and the 'Count' field is set to "-".
- If the command is "long" or "short", the corresponding 'State' field is set to "open" and the 'Count' field is incremented by 1.

4. Sending a PineConnector command: When a webhook is received with a command to send to PineConnector, the command is sent based on the 'Trend' and 'State' fields for the symbol. The specific rules are:
- If the command is "long" and the 'Trend' is "up" and the 'State Long' is "closed" (or if CHECK_STATE is False), a "long" command is sent.
- If the command is "short" and the 'Trend' is "down" and the 'State Short' is "closed" (or if CHECK_STATE is False), a "short" command is sent.
- If 'BB' is in either 'State Long' or 'State Short' fields, the command is not sent.

5. Handling Long and Short positions separately: The 'State Long', 'State Short', 'Count Long', and 'Count Short' fields allow handling long and short positions for a symbol separately. Depending on whether the command is "long" or "short", the corresponding 'State' and 'Count' fields are updated.