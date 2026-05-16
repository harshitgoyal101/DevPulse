import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.factories import UserFactory


@pytest.mark.django_db
class TestAuthAPI:
    def test_me_requires_auth(self):
        client = APIClient()
        response = client.get(reverse("auth_me"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_returns_user(self):
        user = UserFactory(email="me@example.com", password="secret123")
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(reverse("auth_me"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == "me@example.com"
        assert str(response.data["id"]) == str(user.pk)

    def test_token_and_refresh_rotation(self):
        UserFactory(email="tok@example.com", password="secret123")
        client = APIClient()
        obtain = client.post(
            reverse("token_obtain_pair"),
            {"email": "tok@example.com", "password": "secret123"},
            format="json",
        )
        assert obtain.status_code == status.HTTP_200_OK
        refresh = obtain.data["refresh"]

        refreshed = client.post(
            reverse("token_refresh"),
            {"refresh": refresh},
            format="json",
        )
        assert refreshed.status_code == status.HTTP_200_OK
        new_refresh = refreshed.data["refresh"]
        assert new_refresh != refresh

        old = client.post(
            reverse("token_refresh"),
            {"refresh": refresh},
            format="json",
        )
        assert old.status_code == status.HTTP_401_UNAUTHORIZED

        access = refreshed.data["access"]
        me = client.get(reverse("auth_me"), HTTP_AUTHORIZATION=f"Bearer {access}")
        assert me.status_code == status.HTTP_200_OK
