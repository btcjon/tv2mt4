Rather than have many types of incoming messages, I will ensure incoming messages have the following syntax.
This will make parsing messages more simple and flexible.

I will explicitly map information inside the message with '=' with each information seperated by comma.

Here are definitions:

Common to any:

    type: the type of message.  currently can only be 'update' or 'order'
        example1: type=update 
        example2: type=order
        update: message is only used to update airtable
        order: message is meant to go through our filters and if passes goto pineconnector

    symbol: the symbol
        example1: symbol=EURNZD
        example2: symbol=EURNZD.PRO

Only found in type=update messages

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

    Examples of incoming type=update messages
        example1: type=update,symbol=EURNZD,keyword=up
        example2: type=update,symbol=EURNZD,keyword=up,tf=1H
        example3: type=update,symbol=USDCAD.PRO,keyword=TD9buyOn,tf=1H    
        example4: type=update,symbol=USDCAD,keyword=support

    Fields in Airtable to update:
    
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

Only found in type=order messages
    
    order-type: defines the type of order
        example1: order-type=long
        example2: order-type=short
        example3: order-type=closelong
        example4: order-type=closeshort

    risk: defines the risk in an order
        example1: risk=1
        example2: risk=0.3
    
    sl: defines stop loss
        example1: sl=0.1
        example2: sl=0.05
    
    tp: defines take profit
        example1: tp=0.08
        example2: tp=0.1

    comment: defines the order comment
        example1: comment="7-0-30"
    

    Examples of incoming type=order messages
        example1: type=order,order-type=long,symbol=EURNZD.PRO,risk=1,comment="7-0-30"
        example2: type=order,order-type=closelong,symbol=EURNZD.PRO,comment="7-0-30"
        example3: type=order,order-type=long,symbol=EURNZD.PRO,risk=1,tp=0.08,comment="7-0-30"
        example4: type=order,order-type=long,symbol=EURNZD.PRO,risk=1,tp=0.08,sl=0.1,comment="7-0-30"



Handling type=order messages:

type=order messages are meant to be sent to pineconnector ONLY if they pass the following conditions:

config.py will determine if the condition is "true" or "false" 
    if set to true, then condition must be met. If false, you can ignore the condition.

List of conditions in config.py 

    CHECK_STATE = True

        If 'long' check 'State Long', if there is 'BB' then do not send
        If 'short' check 'State Short', if there is 'BB' then do not send

       
    FILTER_SNR = True

        If 'long' order type then 'Resistance' must be 'false'
        If 'short' order type then 'Support' must be 'false'

    FILTER_TD9 = True

        If 'long' order type then TD9sell must be 'false'
        If 'short' order type then TD9buy must be 'false'

    FILTER_TREND = True

        If 'long' order type then Trend must be 'up'
        If 'short' order type then Trend must be 'down'
    
    FILTER_TIME = True

        Time Restriction: NONE should ever be sent to pineconnector during this time:
            # Get the current server time
            now = datetime.utcnow().time()

            # Define the start and end of the restricted period in UTC
            start = time(21, 55)  # 9:55 PM UTC
            end = time(23, 0)  # 11:00 PM UTC

            # Check if the current time is within the restricted period
            if start <= now <= end:
                return  # If it is, do not send any commands to PineConnector


    order-type=closelong = send immediately if passes Time Restriction and BB Restriction
        MUST be sent to pineconnector in following format (raw text): ID,closelong,symbol,comment
        Example = 6700960415957,closelong,EURAUD,comment="7-0-30"

    order-type=closeshort = send immediately if passes Time Restriction and BB Restriction
        MUST be sent to pineconnector in following format (raw text): ID,closeshort,symbol,comment
        Example = 6700960415957,closeshort,EURAUD,comment="7-0-30"

    order-type=long: sending rules below...
        1. IF Long# field is greater than '0' send immediately, otherwise respect the following filters,
        2. Trend = up
        3. Resistance = false
        4. TD9sell = false
            MUST be sent to pineconnector in following format (raw text): ID,long,symbol,risk,comment (note tp and sl are optional)
            Example = 6700960415957,long,EURAUD,risk=1,comment="7-0-30" (note tp and sl are optional)
            Example = 6700960415957,long,EURAUD,risk=1,tp=0.07,sl=0.1,comment="7-0-30"
    
    order-type=short: sending rules below...
        1. IF Short# field is greater than '0' send immediately, otherwise respect the following filters,
        2. Trend = down
        3. Support = false
        4. TD9buy = false
            MUST be sent to pineconnector in following format (raw text): ID,short,symbol,risk,comment (note tp and sl are optional)
            Example = 6700960415957,short,EURAUD,risk=1,comment="7-0-30" (note tp and sl are optional)
            Example = 6700960415957,short,EURAUD,risk=1,tp=0.07,sl=0.1,comment="7-0-30"


Updating Airtable fields after type=order message is successfully sent:

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



Additional Order Type messages that we need to add logic to handle

the string below is order-type=long but our logic is not yet capable of parsing it correctly
6700960415957,long,XAUUSD.PRO,risk=0.1,comment=”Sv3-1”

the string below is order-type=short but our logic is not yet capable of parsing it correctly
6700960415957,short,XAUUSD.PRO,risk=0.1,comment=”Sv3-1”

the string below is order-type=closelong but our logic is not yet capable of parsing it correctly
6700960415957,closelong,XAUUSD.PRO,comment=”Sv3-1”

the string below is order-type=closeshort but our logic is not yet capable of parsing it correctly
6700960415957,closeshort,XAUUSD.PRO,comment=”Sv3-1”

Refactor code to recognize the messages above, parse them correctly, and send them to pineconnector correctly without breaking current code or logic.

