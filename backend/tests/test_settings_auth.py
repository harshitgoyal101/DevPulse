from datetime import timedelta

from django.conf import settings


def test_jwt_access_lifetime_matches_prd():
    access = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
    refresh = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
    assert access == timedelta(minutes=15)
    assert refresh == timedelta(days=7)
    assert settings.SIMPLE_JWT["ROTATE_REFRESH_TOKENS"] is True
    assert settings.SIMPLE_JWT["BLACKLIST_AFTER_ROTATION"] is False
