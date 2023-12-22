from datetime import time

AIRTABLE_API_KEY = 'key8E4aVpJpRArGyw'
AIRTABLE_BASE_ID = 'app2hV8yClkObvn6v'
AIRTABLE_TABLE_NAME = 'table1'
NGROK_AUTH_TOKEN = '2RQAN658II3AIdb9t09ogLi1wJ4_2JATXbhEEYRhzrSuJraBv'
PINECONNECTOR_WEBHOOK_URL = 'https://pineconnector.net/webhook/'
PINECONNECTOR_LICENSE_ID = '6700960415957'
CHECK_STATE = True
FILTER_SNR = True # filter by SNR
FILTER_TD9 = True # filter by TD9
FILTER_TREND = True # filter by trend up or down
FILTER_TIME = True # make sure to not send orders as defined start and end of the restricted period in UTC 
BB_Filter = True # check either state fileds for existence of this and dont send if it exists
FILTER_TIME_START = time(21, 55)  # 9:55 PM UTC
FILTER_TIME_END = time(23, 0)  # 11:00 PM UTC
