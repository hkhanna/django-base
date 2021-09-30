from django.urls import reverse
from django.conf import settings


def test_terms(client):
    """Access Terms of Use page"""
    response = client.get(reverse("terms_of_use"))
    assert response.status_code == 200
    assert "Last Modified" in str(response.content)


def test_privacy(client):
    """Access Privacy Policy page"""
    response = client.get(reverse("privacy_policy"))
    assert response.status_code == 200
    assert "Last Modified" in str(response.content)
