Various incoming webhook text messages in various short text message formats incoming.

Our system then parses the messages to determine actions to take involving reading and updating airtable as well as sending messages to PineConnector service via webhook a raw body text.

1. Updating the 'SnR' field:
   The application updates the 'SnR' (Support and Resistance) field in Airtable based on specific keywords found in the incoming webhook messages. When a message contains phrases like "enters Support" or "enters Resistance," the application identifies the symbol from the message and updates the corresponding 'SnR' field in Airtable to "Support" or "Resistance," respectively. If a message indicates that a symbol "is breaking," the 'SnR' field is cleared.

   Sample incoming messages that prompt 'SnR' field update:
   1. EURAUD - Price enters D Support Zone
   2. NZDCAD - Price enters D Resistance Zone
   3. CHFJPY - Price is breaking out 4h Resistance
   4. USDCHF - Price is breaking down 4h Support

2. Updating the 'Trend' field:
   The 'Trend' field in Airtable is updated when the incoming webhook message contains a command such as "up," "down," or "flat." The application parses the message, extracts the symbol and the trend direction, and updates the 'Trend' field in Airtable with the new value. This allows the system to track the current trend direction for each symbol.

   Sample incoming messages that prompt 'Trend' field update:
   1. 6700960415957,up,EURCHF
   2. 6700960415957,down,EURCHF
   3. 6700960415957,flat,EURCHF

3. Updating the '1H TD9buy' and '1H TD9sell' fields:
   The application updates the '1H TD9buy' and '1H TD9sell' fields in Airtable based on specific keywords found in the incoming webhook messages. When a message contains phrases like "1H TD9buy Symbol" or "1H TD9sell Symbol," the application identifies the symbol from the message and updates the corresponding field in Airtable to 'true'. If a message contains phrases like "1H TD9buy OFF Symbol" or "1H TD9sell OFF Symbol," the application updates the corresponding field in Airtable to 'false'.

   Sample incoming messages that prompt '1H TD9buy' and '1H TD9sell' field update:
   1. 1H TD9buy EURCAD
   2. 1H TD9sell EURCAD
   3. 1H TD9buy OFF EURCAD
   4. 1H TD9sell OFF EURCAD

   These messages only update the '1H TD9buy' and '1H TD9sell' fields in Airtable and do not send any commands to PineConnector.

4. Sending a PineConnector command via webhook:
   When the application receives a webhook message with a trading command ("long" or "short"), it constructs a command string to be sent to PineConnector. The command includes the license ID, the action to be taken (long or short), the symbol, and any additional parameters such as risk, take profit (tp), stop loss (sl), and a comment. This command is then sent to the PineConnector webhook URL. If the PineConnector service successfully processes the command, the application proceeds to update the Airtable with the new state and count. 

   Before sending a command to PineConnector, the application performs several checks:
   - **Time Restriction:** The application does not send any commands to PineConnector between 9:55 PM and 11:00 PM UTC (Converted from EST server time).
   - **'BB' Field Restriction:** The application checks the 'BB' field in Airtable. If the 'BB' field is present for a given symbol, the application does not send any commands to PineConnector for that symbol. This restriction applies to all commands except 'closelong' and 'closeshort', which are sent to PineConnector directly without checking the 'BB' field.
   - **State, Trend, and SnR Checks:** For 'long' and 'short' commands, the application checks the 'State Long' or 'State Short', 'Trend', and 'SnR' fields in Airtable. If these fields do not meet certain conditions, the application does not send the command to PineConnector.

   Sample incoming messages that prompt Sending a Pineconnector command:
   1. 6700960415957,short,NZDCAD.PRO,risk=1,comment="7-0-30"
   2. 6700960415957,short,NZDCAD.PRO,risk=1,tp=0.08,comment="7-0-30"
   3. 6700960415957,short,NZDCAD.PRO,risk=1,tp=0.08,sl=0.1,comment="7-0-30"
   4. 6700960415957,long,USDCHF.PRO,risk=1,comment="7-0-30"
   5. 6700960415957,closeshort,EURUSD.PRO,comment="7-0-30"
   6. 6700960415957,closelong,EURUSD.PRO,comment="7-0-30"

5. Updating of 'State Long' and 'State Short':
   After sending a command to PineConnector, the application updates the 'State Long' or 'State Short' field in Airtable, depending on whether the command was to go long or short. This field represents the current state of the trade for the symbol. Additionally, the application increments the 'Count Long' or 'Count Short' field, which keeps track of the number of times a long or short command has been issued for the symbol.

