#Tests to check the api calls being made by the script
import pytest
import requests
import json
import time
import logging
import responses
from collectioncode import utils, collect
from mock import Mock, patch




#Setting up the vars for use in the api calls
baseurl = "https://10.135.7.222/restconf"
# uri = "/data/v1/cisco-resource-network:topological-link?topo-layer=ots-link-layer&.startIndex=0"
# Updating URI to fix the performance tac case
uri = "/data/v1/cisco-resource-network:topological-link?topo-layer=ots-link-layer&.skipFiberAttributes=true&.skipPerformanceMetrics=true&.startIndex=0"
user = 'root'
password = 'Epnm1234'
Logger = logging.getLogger(__name__)

def setup_module(utils):
    collect.thread_data.logger = Logger

#The test names should be description enough
def test_api_get_successful_response():

    circuit_breaker1 = utils.Circuit_breaker(timeout_limit=15)
    response = circuit_breaker1.request(baseurl, uri, user, password)
    assert len(response) > 0

#Setting the timeout value low to force the exception
def test_api_timeout_return_null():

    circuit_breaker1 = utils.Circuit_breaker(timeout_limit=0)
    # with pytest.raises(Exception):
    #     assert circuit_breaker1.request(baseurl, uri, user, password)
    response = circuit_breaker1.request(baseurl, uri, user, password)
    assert response == '[]'

#Delaying for the max amount of 60 seconds
def test_api_for_none_timeout_value():
    resp1 = {
        "test": ["Not empty"]
    }
    baseurl = "https://run.mocky.io/v3/fca0a56e-29b0-41fc-8f2d-5ad7f5eed27e"
    uri = "?mocky-delay=20s"

    circuit_breaker1 = utils.Circuit_breaker(timeout_limit=None)
    response = circuit_breaker1.request(baseurl, uri, user, password)
    assert json.loads(response) == resp1

#Delaying for the max amount of 60 seconds
def test_api_for_bad_timeout_value_with_max_delay():
    baseurl = "https://run.mocky.io/v3/fca0a56e-29b0-41fc-8f2d-5ad7f5eed27e"
    uri = "?mocky-delay=20s"

    circuit_breaker1 = utils.Circuit_breaker(timeout_limit=5)
    response = circuit_breaker1.request(baseurl, uri, user, password)
    assert response == '[]'

#Delaying for the max amount of 60 seconds
def test_api_for_good_timeout_value_with_max_delay():
    resp1 = {
        "test": ["Not empty"]
    }
    baseurl = "https://run.mocky.io/v3/fca0a56e-29b0-41fc-8f2d-5ad7f5eed27e"
    uri = "?mocky-delay=20s"

    circuit_breaker1 = utils.Circuit_breaker(timeout_limit=30)
    response = circuit_breaker1.request(baseurl, uri, user, password)
    assert json.loads(response) == resp1

# @responses.activate
# def test_api_for_none_timeout_value():

#     resp1 = {
#         "test": ["Not empty"]
#     }

#     def request_callback(request):
#         time.sleep(5)
#         return(200, 'header', resp1)

#     responses.add_callback(responses.GET, baseurl + uri, callback=request_callback)
#     circuit_breaker1 = utils.Circuit_breaker(timeout_limit=10)
#     response = circuit_breaker1.request(baseurl, uri, user, password)
#     assert response.json() == resp1
    
# @patch.object(requests, 'get')
# def test_api_for_none_timeout_value(mock_request):

#     resp1 = {
#         "test": ["Not empty"]
#     }

#     def waiting():
#         time.sleep(15)
#         return resp1

#     mockResponse = Mock()
#     mockResponse.json.return_value = resp1
#     mockResponse.status_code = 200
#     mock_request.return_value = mockResponse
#     mock_request.side_effect = waiting()

#     circuit_breaker1 = utils.Circuit_breaker(timeout_limit=30)
#     response = circuit_breaker1.request(baseurl, uri, user, password)
#     assert json.loads(response) == resp1

@patch.object(requests, 'get')
def test_api_for_nonempty_response(mock_request):

    resp1 = {
        "test": ["Not empty"]
    }
    mockResponse = Mock()
    mockResponse.json.return_value = resp1
    mockResponse.status_code = 200
    mock_request.return_value = mockResponse

    circuit_breaker1 = utils.Circuit_breaker()
    response = circuit_breaker1.request(baseurl, uri, user, password)
    assert json.loads(response) == resp1

@patch.object(requests, 'get')
def test_api_for_empty_response(mock_request):

    resp1 = {
        "test": []
    }
    mockResponse = Mock()
    mockResponse.json.return_value = resp1
    mockResponse.status_code = 200
    mock_request.return_value = mockResponse

    circuit_breaker1 = utils.Circuit_breaker()
    response = circuit_breaker1.request(baseurl, uri, user, password)
    assert response == '[]'

@patch.object(requests, 'get')
def test_api_for_error_status_code(mock_request):

    resp1 = {
        "test": ["Not empty"]
    }
    mockResponse = Mock()
    mockResponse.json.return_value = resp1
    mockResponse.status_code = 400
    mock_request.return_value = mockResponse

    circuit_breaker1 = utils.Circuit_breaker()
    response = circuit_breaker1.request(baseurl, uri, user, password)
    assert response == '[]'