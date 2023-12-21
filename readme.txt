Incoming messages will adhere to a standardized syntax for simplicity and flexibility in parsing.

Message information will be key-value paired using '=' and separated by commas.

Here are definitions:

Common to all messages:

    type: the type of message.  currently can only be 'update' or 'order'
        example1: type=update 
        example2: type=order
        update: message is only used to update airtable
        order: message is meant to go through our filters and if passes goto pineconnector

    symbol: the symbol
        example1: symbol=EURNZD
        example2: symbol=EURNZD.PRO

Specific to type=update messages:

    keyword: let's us know what needs to be updated
        example1: keyword=TD9buyOn 
        example2: keyword=TD9buyOff
        example3: keyword=support
        example4: keyword=resistance
        example5: keyword=up
        example6: keyword=down
    
    tf: time-frame of update
        example1: tf=1H
        example2: tf=30M
        example3: tf=1D

    Example type=update messages:
        example1: type=update,symbol=EURNZD,keyword=up
        example2: type=update,symbol=EURNZD,keyword=up,tf=1H
        example3: type=update,symbol=USDCAD.PRO,keyword=TD9buyOn,tf=1H    
        example4: type=update,symbol=USDCAD,keyword=support

    Airtable fields to update:
    
    Resistance (boolean)
        type=update AND any of the following:
        keyword=resistance (true)
        keyword=resistanceOFF (false)
    
    Support (boolean)
        type=update AND any of the following:
        keyword=support (true)
        keyword=supportOFF (false)
    
    TD9buy (boolean)
        type=update AND any of the following:
        keyword=TD9buy (true)
        keyword=TD9buyOFF (false)
    
    TD9sell (boolean)
        type=update AND any of the following:
        keyword=TD9sell (true)
        keyword=TD9sellOFF (false)
    
    Trend (text)
        type=update AND any of the following:
        keyword=up (change Trend field to 'up')
        keyword=down (change Trend field to 'down')

    BB (boolean) (not to be updated but to be checked in event of BB_Filter = True)
        keyword=BB (true)
        keyword=BBOFF (false)

Specific to type=order messages:
    
    order-type: defines the type of order
        example1: order-type=long
        example2: order-type=short
        example3: order-type=closelong
        example4: order-type=closeshort

    risk: defines the risk in an order (required for order-type=long and order-type=short)
        example1: risk=1
        example2: risk=0.3
    
    sl: defines stop loss (optional and only applies to order-type=long and order-type=short)
        example1: sl=0.1
        example2: sl=0.05
    
    tp: defines take profit (optional and only applies to order-type=long and order-type=short)
        example1: tp=0.08
        example2: tp=0.1
    
    entry: defines if it is an entry order or not (entry orders follow stricter filtering than entry=false)
        example1: entry=true
        example2: entry=false

    comment: defines the order comment
        example1: comment="7-0-30"
    

    Example type=order messages:
        example1: type=order,order-type=long,symbol=EURNZD.PRO,risk=1,comment="7-0-30",entry=true
        example2: type=order,order-type=closelong,symbol=EURNZD.PRO,comment="7-0-30"
        example3: type=order,order-type=long,symbol=EURNZD.PRO,risk=1,tp=0.08,comment="7-0-30"
        example4: type=order,order-type=long,symbol=EURNZD.PRO,risk=1,tp=0.08,sl=0.1,comment="7-0-30",entry=false

Handling of type=order messages:

type=order messages are meant to be sent to PineConnector only if they pass the following conditions:

    entry: indicates whether the order should bypass certain filters
        - If entry=true, the order must pass all active filters as defined in the config.py settings.
        - If entry=false, the order bypasses all filters except for FILTER_TIME and BB_Filter and is sent to PineConnector immediately.

Time Restriction: No orders should be sent to PineConnector during:
    # Get the current server time
    now = datetime.utcnow().time()

    # Define the start and end of the restricted period in UTC
    start = time(21, 55)  # 9:55 PM UTC
    end = time(23, 0)  # 11:00 PM UTC

    # Check if the current time is within the restricted period
    if start <= now <= end:
        return  # If it is, do not send any commands to PineConnector

BB Restriction: No orders should be sent if 'BB' is present in 'State Long' or 'State Short' fields.

    order-type=closelong = send immediately if passes Time Restriction and BB Restriction
        MUST be sent to pineconnector in following format (raw text): ID,closelong,symbol,comment
        Example = 6700960415957,closelong,EURAUD,comment="7-0-30"

    order-type=closeshort = send immediately if passes Time Restriction and BB Restriction
        MUST be sent to pineconnector in following format (raw text): ID,closeshort,symbol,comment
        Example = 6700960415957,closeshort,EURAUD,comment="7-0-30"

    For order-type=long and order-type=short:
        - Orders are sent to PineConnector in the following format (raw text): ID,order-type,symbol,risk,comment (note tp and sl are optional)
        - Examples:
            - 6700960415957,long,EURAUD,risk=1,comment="7-0-30"
            - 6700960415957,short,EURAUD,risk=1,tp=0.07,sl=0.1,comment="7-0-30"
        - The FILTER_TIME and BB_Filter checks are applied. Additional filters are applied based on the 'entry' parameter.


Post-order Airtable field updates:

State Long
    1. if order-type=long was sent change field to 'open' (if it is not already)
    2. if order-type=closelong was sent change field to 'closed'
State Short
    1. if order-type=short was sent change field to open (if it is not already)
    2. if order-type=closeshort was sent change field to 'closed'
Long#
    1. if order-type=long was sent, increment the number by '1'
    2. if order-type=closelong was sent, change number to '0'
Short#
    1. if order-type=short was sent, increment the number by '1'
    2. if order-type=closeshort was sent, change number to '0'

    Handling of the USTEC100 symbol:
        - If the symbol is 'NAS100' or 'NAS100.PRO', it is replaced with 'USTEC100' before processing.

    Retry Logic for Airtable Updates:
        - In case of a connection error when updating Airtable fields, the system will wait for 5 seconds and retry the update.

    Time Restriction Configuration:
        - The start and end times for the restricted period can be overridden by `FILTER_TIME_START` and `FILTER_TIME_END` in `config.py`.

    BB Filter Configuration:
        - The presence of 'BB' in Airtable fields can be used as a filter based on the `BB_Filter` setting in `config.py`.

    Incrementing and Resetting Long# and Short#:
        - After sending an order of type 'long', the 'Long#' field is incremented by 1.
        - After sending an order of type 'closelong', the 'Long#' field is reset to 0.
        - After sending an order of type 'short', the 'Short#' field is incremented by 1.
        - After sending an order of type 'closeshort', the 'Short#' field is reset to 0.
