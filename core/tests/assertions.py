from django.contrib.messages import get_messages


def assertMessageContains(response, expected):
    messages = list(get_messages(response.wsgi_request))
    assert len(messages) > 0, "No messages found"
    actual = str(messages[-1])
    assert expected in actual
