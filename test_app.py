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

# Test cases for update messages
def test_update_message_resistance_on(client):
    data = 'type=update,symbol=XAGUSD,keyword=resistance'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200

def test_update_message_resistance_off(client):
    data = 'type=update,symbol=XAGUSD,keyword=resistanceOFF'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200

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

# Test cases for order messages
def test_order_message_short(client):
    data = 'type=order,order-type=short,symbol=XAUUSD.PRO,risk=0.1,comment="Sv3-1"'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200

def test_order_message_closeshort(client):
    data = 'type=order,order-type=closeshort,symbol=XAUUSD.PRO,comment="Sv3-1"'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200

def test_order_message_with_tp_sl(client):
    data = 'type=order,order-type=long,symbol=XAUUSD.PRO,risk=1,tp=0.08,sl=0.1,comment="7-0-30"'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200

# Test cases for new order format
def test_new_order_format_long(client):
    data = '6700960415957,long,XAUUSD.PRO,risk=0.1,comment="Sv3-1"'
    response = client.post('/webhook', data=data)
    assert response.status_code == 200

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
