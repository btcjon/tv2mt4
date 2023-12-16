import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_update_message_with_TD9buy(client):
    # Define the message data for an update message with TD9buy keyword
    data = 'type=update,symbol=XAGUSD,keyword=TD9buy'
    # Simulate a POST request to the webhook endpoint
    response = client.post('/webhook', data=data)
    # Assert that the response status code is 200
    assert response.status_code == 200
    # Additional assertions can be made here, such as checking the response data

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

# More test cases can be added here to cover different scenarios and message formats
