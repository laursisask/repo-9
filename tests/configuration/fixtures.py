import pytest
from tap_mixpanel.client import MixpanelClient


@pytest.fixture
def mixpanel_client():
    mixpanel_client = MixpanelClient('API_SECRET', 'username', 'password', 'project_id')
    mixpanel_client._MixpanelClient__verified = True
    return mixpanel_client
