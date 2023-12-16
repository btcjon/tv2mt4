import pytest
from unittest.mock import patch
from app import app, AirtableOperations

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch.object(AirtableOperations, 'update_airtable_field')
def test_update_message_with_TD9buy(mock_update_airtable_field, client):
    # Define the message data for an update message with TD9buy keyword
    data = 'type=update,symbol=XAGUSD,keyword=TD9buy'
    # Simulate a POST request to the webhook endpoint
    response = client.post('/webhook', data=data)
    # Assert that the response status code is 200
    assert response.status_code == 200
    # Assert that the Airtable API was called with the correct parameters
    mock_update_airtable_field.assert_called_once_with('XAGUSD', 'TD9buy', True)

def test_order_message_long(client):
    # Define the message data for an order message with long order-type
    data = 'type=order,order-type=long,symbol=XAUUSD.PRO,risk=0.1,comment="Sv3-1"'
    # Simulate a POST request to the webhook endpoint
    response = client.post('/webhook', data=data)
    # Assert that the response status code is 200
    assert response.status_code == 200
    # Additional assertions can be made here

def test_order_message_closelong(client):
    # Define the message data for an order message with closelong order-type
    data = 'type=order,order-type=closelong,symbol=XAUUSD.PRO,comment="Sv3-1"'
    # Simulate a POST request to the webhook endpoint
    response = client.post('/webhook', data=data)
    # Assert that the response status code is 200
    assert response.status_code == 200
    # Additional assertions can be made here

# Test cases for update messages with all possible keywords
@pytest.mark.parametrize("keyword, field, value", [
    ('resistance', 'Resistance', True),
    ('resistanceOFF', 'Resistance', False),
    ('support', 'Support', True),
    ('supportOFF', 'Support', False),
    ('TD9buy', 'TD9buy', True),
    ('TD9buyOFF', 'TD9buy', False),
    ('TD9sell', 'TD9sell', True),
    ('TD9sellOFF', 'TD9sell', False),
    ('up', 'Trend', 'up'),
    ('down', 'Trend', 'down'),
])
def test_update_messages(client, keyword, field, value):
    data = f'type=update,symbol=XAGUSD,keyword={keyword}'
    with patch.object(AirtableOperations, 'update_airtable_field') as mock_update_airtable_field:
        response = client.post('/webhook', data=data)
        assert response.status_code == 200
        mock_update_airtable_field.assert_called_once_with('XAGUSD', field, value)

def test_update_message_support_on(client):
    data = 'type=update,symbol=XAGUSD,keyword=support'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200

def test_update_message_support_off(client):
    data = 'type=update,symbol=XAGUSD,keyword=supportOFF'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200

def test_update_message_TD9sell_on(client):
    data = 'type=update,symbol=XAGUSD,keyword=TD9sell'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200

def test_update_message_TD9sell_off(client):
    data = 'type=update,symbol=XAGUSD,keyword=TD9sellOFF'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200

def test_update_message_trend_up(client):
    data = 'type=update,symbol=XAGUSD,keyword=up'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200

def test_update_message_trend_down(client):
    data = 'type=update,symbol=XAGUSD,keyword=down'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200

# Test cases for order messages with all possible order types and conditions
@pytest.mark.parametrize("order_type, symbol, risk, comment, time_restricted, bb_present, trend, resistance, td9sell, support, td9buy, expected_call_count", [
    # Add various combinations of parameters to test different scenarios
    # Example: ('long', 'XAUUSD.PRO', '0.1', 'Sv3-1', False, False, 'up', False, False, False, False, 1),
    # Add more test cases here...
])
@patch.object(AirtableOperations, 'get_matching_record')
@patch('app.send_pineconnector_command')
def test_order_messages(mock_send_pineconnector_command, mock_get_matching_record, client, order_type, symbol, risk, comment, time_restricted, bb_present, trend, resistance, td9sell, support, td9buy, expected_call_count):
    # Mock the current time to control the time restriction
    with patch('app.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = datetime(2020, 1, 1, 22, 0)  # Set to a time within the restricted period
        # Mock the Airtable record to control the BB restriction and other filters
        mock_get_matching_record.return_value = {
            'fields': {
                'BB': bb_present,
                'Trend': trend,
                'Resistance': resistance,
                'TD9sell': td9sell,
                'Support': support,
                'TD9buy': td9buy,
            }
        }
        data = f'type=order,order-type={order_type},symbol={symbol},risk={risk},comment={comment}'
        response = client.post('/webhook', data=data)
        assert response.status_code == 200
        if time_restricted:
            mock_send_pineconnector_command.assert_not_called()
        else:
            assert mock_send_pineconnector_command.call_count == expected_call_count

def test_order_message_closeshort(client):
    data = 'type=order,order-type=closeshort,symbol=XAUUSD.PRO,comment="Sv3-1"'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200

def test_order_message_with_tp_sl(client):
    data = 'type=order,order-type=long,symbol=XAUUSD.PRO,risk=1,tp=0.08,sl=0.1,comment="7-0-30"'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200

# Test cases for new order format messages
@pytest.mark.parametrize("order_id, order_type, symbol, risk, comment", [
    ('6700960415957', 'long', 'XAUUSD.PRO', '0.1', 'Sv3-1'),
    ('6700960415957', 'short', 'XAUUSD.PRO', '0.1', 'Sv3-1'),
    ('6700960415957', 'closelong', 'XAUUSD.PRO', None, 'Sv3-1'),
    ('6700960415957', 'closeshort', 'XAUUSD.PRO', None, 'Sv3-1'),
    # Add more test cases here...
])
@patch('app.send_pineconnector_command')
def test_new_order_format_messages(mock_send_pineconnector_command, client, order_id, order_type, symbol, risk, comment):
    data = f'{order_id},{order_type},{symbol},risk={risk},comment={comment}'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200
    mock_send_pineconnector_command.assert_called_once_with(order_id, order_type, symbol, risk, None, None, comment)

def test_new_order_format_short(client):
    data = '6700960415957,short,XAUUSD.PRO,risk=0.1,comment="Sv3-1"'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200

def test_new_order_format_closelong(client):
    data = '6700960415957,closelong,XAUUSD.PRO,comment="Sv3-1"'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200

def test_new_order_format_closeshort(client):
    data = '6700960415957,closeshort,XAUUSD.PRO,comment="Sv3-1"'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200

def test_update_message_with_TD9buy(client):
    # Define the message data for an update message with TD9buy keyword
    data = 'type=update,symbol=XAGUSD,keyword=TD9buy'
    # Simulate a POST request to the webhook endpoint
    response = client.post('/webhook', data=data)
    # Assert that the response status code is 200
    assert response.status_code == 200
    # Additional assertions can be made here, such as checking the response data

# More test cases can be added here to cover different scenarios and message formats
