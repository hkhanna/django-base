from django.contrib.messages import get_messages


def assertMessageContains(response, message):
    messages = list(get_messages(response.wsgi_request))
    assert message in str(messages[-1])
