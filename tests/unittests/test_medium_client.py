from collections.abc import Generator
from unittest import mock

import requests
import requests_mock

import pytest
from pytest import raises
from tap_mixpanel import client
from tap_mixpanel.client import ReadTimeoutError, Server5xxError, MixpanelRateLimitsError
from tests.configuration.fixtures import mixpanel_client


@mock.patch('time.sleep', return_value=None)
def test_request_export_backoff_on_timeout(mock_sleep, mixpanel_client):
    with requests_mock.Mocker() as m:
        m.request('GET', 'http://test.com', exc=requests.exceptions.Timeout('Timeout on request'))

        with raises(ReadTimeoutError) as ex:
            for record in mixpanel_client.request_export('GET', url='http://test.com'):
                pass
        # Assert backoff retry count as expected    
        assert mock_sleep.call_count == client.BACKOFF_MAX_TRIES_REQUEST - 1


@pytest.mark.parametrize(
    'status_code,exception,response_json',
    [
        pytest.param(504, Server5xxError, None, id="Server5xxError"),
        pytest.param(429, MixpanelRateLimitsError, {'error': 'Too Many Requests', 'status': 429}, id="MixpanelRateLimitsError"),
    ],
)
@mock.patch('time.sleep', return_value=None)
def test_request_export_backoff_on_remote_timeout(mock_sleep, mixpanel_client, status_code, exception, response_json):
    with requests_mock.Mocker() as m:
        m.request('GET', 'http://test.com', content=None, json=response_json, status_code=status_code)
        result = mixpanel_client.request_export('GET', url='http://test.com')

        with raises(exception) as ex:
            for record in result:
                pass
        # Assert backoff retry count as expected    
        assert mock_sleep.call_count == client.BACKOFF_MAX_TRIES_REQUEST - 1

@mock.patch('time.sleep', return_value=None)
def test_request_backoff_on_timeout(mock_sleep, mixpanel_client):
    with requests_mock.Mocker() as m:
        m.request('GET', 'http://test.com', exc=requests.exceptions.Timeout('Timeout on request'))
        
        with raises(ReadTimeoutError) as ex:
            result = mixpanel_client.request('GET', url='http://test.com')

        # Assert backoff retry count as expected    
        assert mock_sleep.call_count == client.BACKOFF_MAX_TRIES_REQUEST - 1

def test_request_returns_json(mixpanel_client):
    with requests_mock.Mocker() as m:
        m.request('GET', 'http://test.com', json={'a': 'b'})
        result = mixpanel_client.request('GET', url='http://test.com')
        assert result == {'a': 'b'}

def test_request_export_returns_generator(mixpanel_client):
    with requests_mock.Mocker() as m:
        m.request('GET', 'http://test.com', json={'a': 'b'})
        result = mixpanel_client.request_export('GET', url='http://test.com')
        assert isinstance(result, Generator)
