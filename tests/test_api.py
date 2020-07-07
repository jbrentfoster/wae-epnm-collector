#Tests to check the api calls being made by the script
import pytest
import requests
import json
from collectioncode import utils
from mock import Mock, patch




#Setting up the vars for use in the api calls
baseurl = "https://10.135.7.222/restconf"
uri = "/data/v1/cisco-resource-network:topological-link?topo-layer=ots-link-layer&.startIndex=0"
user = 'root'
password = 'Epnm1234'

#The test names should be description enough
def test_api_get_successful_response():

    circuit_breaker1 = utils.Circuit_breaker(timeout_limit=15)
    response = circuit_breaker1.request(baseurl, uri, user, password)
    assert len(response) > 0

#Setting the timeout value low to force the exception
def test_api_get_timeout_raised_exception():

    circuit_breaker1 = utils.Circuit_breaker(timeout_limit=1)
    # with pytest.raises(Exception):
    #     assert circuit_breaker1.request(baseurl, uri, user, password)
    response = circuit_breaker1.request(baseurl, uri, user, password)
    assert response == '[]'

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