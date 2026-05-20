import json
from pathlib import Path

import pytest
from django.core.management import call_command

from apps.accounts.models import User
from apps.ingestion.models import BuildEvent, WebhookDelivery
from apps.organizations.models import Organization, OrganizationMembership, Project

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "demo_seed.json"


@pytest.fixture
def seed_data():
    with SEED_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def test_demo_seed_json_is_valid(seed_data):
    assert seed_data["version"] == 1
    assert len(seed_data["users"]) >= 10
    assert len(seed_data["organizations"]) == 4
    for org in seed_data["organizations"]:
        assert org["slug"]
        assert len(org["projects"]) == 10
        assert org["memberships"]
    assert len(seed_data["webhook_deliveries"]) >= 1
    assert len(seed_data["build_events"]) == 40


@pytest.mark.django_db
def test_load_demo_seed_command(seed_data):
    call_command("load_demo_seed")
    assert User.objects.filter(email="alice@acme.dev").exists()
    assert Organization.objects.filter(slug="acme").exists()
    assert Project.objects.filter(slug="web-api", organization__slug="acme").exists()
    assert OrganizationMembership.objects.filter(
        user__email="alice@acme.dev",
        organization__slug="acme",
        role="admin",
    ).exists()
    assert WebhookDelivery.objects.filter(delivery_id="github-acme-delivery-0001").exists()
    assert BuildEvent.objects.filter(branch="main", status="success").exists()
    assert Organization.objects.count() == 4
    assert Project.objects.count() == 40
    assert User.objects.count() == 20

    alice = User.objects.get(email="alice@acme.dev")
    assert alice.check_password(seed_data["default_password"])

    call_command("load_demo_seed")
    assert User.objects.filter(email="alice@acme.dev").count() == 1
