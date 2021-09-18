import json
import urllib.parse
from unittest import mock
from unittest.mock import patch

import pytest
from django.core import mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from django.test import TestCase
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.skip

User = get_user_model()


class ConfirmEmailAPITest(TestCase):
    """Users confirming their email"""

    def setUp(self):
        cache.clear()
        self.user = factories.UserFactory()
        self.client.force_login(self.user)

    def test_resend_email_confirmation(self):
        """User may request another email confirmation"""
        self.assertEqual(models.EmailMessage.objects.count(), 0)
        response = self.client.post(reverse("core:resend-confirm-email"))
        self.assertEqual(response.status_code, 201)
        email = models.EmailMessage.objects.first()
        self.assertEqual(email.created_by, self.user)
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(mail.outbox[0].subject, "Confirm Your Email Address")

    def test_resend_email_throttle(self, *args):
        """Resend email endpoint is throttled"""
        for i in range(5):
            response = self.client.post(reverse("core:resend-confirm-email"))
            self.assertEqual(response.status_code, 201)

        response = self.client.post(reverse("core:resend-confirm-email"))
        self.assertEqual(response.status_code, 429)

    def test_settings_update_email(self):
        """Updating a User's email should unconfirm their email and send them a confirmation email"""
        self.user.is_confirmed_email = True
        self.user.save()
        old_email = self.user.email
        data = {
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "email": "new_email@example.com",
            "password": "goodpass",
        }
        response = self.client.put(reverse("core:user"), data)
        self.assertEqual(response.status_code, 200)
        self.assertNotDataContains(response.data, {"email": old_email})
        self.assertDataContains(response.data, {"email": "new_email@example.com"})
        self.assertDataContains(response.data, {"is_confirmed_email": False})
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(mail.outbox[0].subject, "Confirm Your Email Address")
        self.assertEqual(
            mail.outbox[0].to,
            [f"{self.user.name} <new_email@example.com>"],
        )


class DeleteUserAPITest(TestCase):
    """Deleting a user"""

    def setUp(self):
        self.user = factories.UserFactory()
        Token.objects.create(user=self.user)
        self.client.force_login(self.user)

    def test_user_delete(self):
        """Deleting a user should disable User.is_active"""

        # User's password is usable
        self.assertTrue(
            self.client.login(username=self.user.email, password="goodpass")
        )
        self.assertIsNotNone(self.user.auth_token)

        response = self.client.delete(reverse("core:user"))
        self.assertEqual(204, response.status_code)
        self.user.refresh_from_db()

        # User's password is unusable
        self.assertFalse(
            self.client.login(username=self.user.email, password="goodpass")
        )

        # User.is_active is False
        self.assertFalse(self.user.is_active)

        # auth token has been deleted
        self.assertEqual(Token.objects.count(), 0)

    def test_user_create_after_delete(self):
        """Deleted user signing up again should re-enable is_active"""
        response = self.client.delete(reverse("core:user"))
        self.assertEqual(204, response.status_code)
        self.client.logout()
        user = User.objects.filter(email=self.user.email).first()
        self.assertFalse(user.is_active)
        payload = {
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "email": self.user.email,
            "password": "a really good password!",
            "accept_terms": True,
        }
        response = self.client.post(reverse("core:create-user"), payload)
        self.assertEqual(response.status_code, 201)
        user = User.objects.filter(email=self.user.email).first()
        self.assertIsNotNone(user)
        self.assertTrue(user.is_active)

    def test_deleted_user_login(self):
        """If User.is_active is False, user cannot log in"""
        self.client.logout()
        self.user.is_active = False
        self.user.save()
        response = self.client.post(
            reverse("core:auth-token"),
            {"username": self.user.email, "password": "goodpass"},
        )
        self.assertEqual(response.status_code, 400)

    def test_deleted_user_access(self):
        """If User.is_active is False, user cannot access logged in endpoints"""
        response = self.client.get(reverse("core:user"))
        self.assertEqual(response.status_code, 200)
        self.user.is_active = False
        self.user.save()
        response = self.client.get(reverse("core:user"))
        self.assertEqual(response.status_code, 401)

    def test_deleted_user_unconfirm_email(self):
        """A User with a confirmed email address that gets deleted automatically unconfirms their email.
        This is useful in case they sign up again."""
        self.user.is_confirmed_email = True
        self.user.save()

        response = self.client.delete(reverse("core:user"))
        self.assertEqual(204, response.status_code)
        self.client.logout()
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.is_confirmed_email)

    def test_roll_auth_token(self):
        """A User can delete their auth token"""
        # Make sure an auth token exists
        self.assertTrue(
            self.client.login(username=self.user.email, password="goodpass")
        )
        token = self.user.auth_token
        self.assertIsNotNone(token)

        response = self.client.post(reverse("core:roll-auth-token"))
        self.assertEqual(201, response.status_code)
        self.user.refresh_from_db()

        # Token is not None and not equal to the old token
        self.assertIsNotNone(self.user.auth_token)
        self.assertNotEqual(token, self.user.auth_token)

        # There's only one token in the db. I.e, the old one got deleted.
        self.assertEqual(1, Token.objects.count())
