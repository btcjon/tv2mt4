1. Updating the 'SnR' field:
   The application updates the 'SnR' (Support and Resistance) field in Airtable based on specific keywords found in the incoming webhook messages. When a message contains phrases like "enters Support" or "enters Resistance," the application identifies the symbol from the message and updates the corresponding 'SnR' field in Airtable to "Support" or "Resistance," respectively. If a message indicates that a symbol "is breaking," the 'SnR' field is cleared.

   Sample incoming messages that prompt 'SnR' field update:
   1. EURAUD - Price enters D Support Zone
   2. NZDCAD - Price enters D Resistance Zone
   3. CHFJPY - Price is breaking out 4h Resistance

2. Updating the 'Trend' field:
   The 'Trend' field in Airtable is updated when the incoming webhook message contains a command such as "up," "down," or "flat." The application parses the message, extracts the symbol and the trend direction, and updates the 'Trend' field in Airtable with the new value. This allows the system to track the current trend direction for each symbol.

   Sample incoming messages that prompt 'Trend' field update:
   1. 6700960415957,up,EURCHF
   2. 6700960415957,down,EURCHF
   3. 6700960415957,flat,EURCHF

3. Sending a PineConnector command:
   When the application receives a webhook message with a trading command ("long" or "short"), it constructs a command string to be sent to PineConnector. The command includes the license ID, the action to be taken (long or short), the symbol, and any additional parameters such as risk, take profit (tp), stop loss (sl), and a comment. This command is then sent to the PineConnector webhook URL. If the PineConnector service successfully processes the command, the application proceeds to update the Airtable with the new state and count.

   Sample incoming messages that prompt Sending a Pineconnector command:
   1. 6700960415957,short,NZDCAD.PRO,risk=1,comment="7-0-30"
   2. 6700960415957,short,NZDCAD.PRO,risk=1,tp=0.08,comment="7-0-30"
   3. 6700960415957,short,NZDCAD.PRO,risk=1,tp=0.08,sl=0.1,comment="7-0-30"
   4. 6700960415957,long,USDCHF.PRO,risk=1,comment="7-0-30"
   5. 6700960415957,closeshort,EURUSD.PRO,comment="7-0-30"
   6. 6700960415957,closelong,EURUSD.PRO,comment="7-0-30"

4. Updating of 'State Long' and 'State Short':
   After sending a command to PineConnector, the application updates the 'State Long' or 'State Short' field in Airtable, depending on whether the command was to go long or short. This field represents the current state of the trade for the symbol. Additionally, the application increments the 'Count Long' or 'Count Short' field, which keeps track of the number of times a long or short command has been issued for the symbol.

