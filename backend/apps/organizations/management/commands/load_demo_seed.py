"""Load demo tenants from backend/data/demo_seed.json."""

import json
import uuid
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User
from apps.ingestion.models import BuildEvent, WebhookDelivery
from apps.organizations.models import Organization, OrganizationMembership, Project

SEED_PATH = Path(settings.BASE_DIR) / "data" / "demo_seed.json"


class Command(BaseCommand):
    help = "Create demo users, orgs, projects, memberships, and sample ingestion rows from demo_seed.json."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=Path,
            default=SEED_PATH,
            help=f"Path to seed JSON (default: {SEED_PATH})",
        )
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help="Re-hash default_password for all seed users (useful after changing the JSON password).",
        )

    def handle(self, *args, **options):
        path: Path = options["file"]
        if not path.is_file():
            raise CommandError(f"Seed file not found: {path}")

        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)

        password = data.get("default_password", "demo-password123")
        users_by_email = self._load_users(data.get("users", []), password, options["reset_passwords"])
        projects_by_ref = self._load_organizations(
            data.get("organizations", []),
            users_by_email,
        )
        self._load_webhook_deliveries(data.get("webhook_deliveries", []), projects_by_ref)
        self._load_build_events(data.get("build_events", []), projects_by_ref)

        self.stdout.write(self.style.SUCCESS(f"Demo seed loaded from {path}"))
        self.stdout.write(f"  Users: {len(users_by_email)}")
        self.stdout.write(f"  Projects: {len(projects_by_ref)}")
        self.stdout.write(f"  Default login password: {password}")

    @transaction.atomic
    def _load_users(self, users_data, password, reset_passwords):
        users_by_email = {}
        for row in users_data:
            email = row["email"]
            user_id = uuid.UUID(row["id"])
            defaults = {
                "email": email,
                "first_name": row.get("first_name", ""),
                "last_name": row.get("last_name", ""),
                "is_staff": row.get("is_staff", False),
                "is_active": row.get("is_active", True),
            }
            user, created = User.objects.update_or_create(id=user_id, defaults=defaults)
            if created or reset_passwords:
                user.set_password(password)
                user.save(update_fields=["password"])
            users_by_email[email] = user
            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} user {email}")
        return users_by_email

    @transaction.atomic
    def _load_organizations(self, orgs_data, users_by_email):
        projects_by_ref = {}
        for org_row in orgs_data:
            org, org_created = Organization.objects.update_or_create(
                id=uuid.UUID(org_row["id"]),
                defaults={"name": org_row["name"], "slug": org_row["slug"]},
            )
            action = "Created" if org_created else "Updated"
            self.stdout.write(f"  {action} org {org.slug}")

            for proj_row in org_row.get("projects", []):
                project, proj_created = Project.objects.update_or_create(
                    id=uuid.UUID(proj_row["id"]),
                    defaults={
                        "organization": org,
                        "name": proj_row["name"],
                        "slug": proj_row["slug"],
                    },
                )
                ref = (org.slug, project.slug)
                projects_by_ref[ref] = project
                action = "Created" if proj_created else "Updated"
                self.stdout.write(f"    {action} project {org.slug}/{project.slug}")

            for mem_row in org_row.get("memberships", []):
                email = mem_row["user_email"]
                user = users_by_email.get(email)
                if user is None:
                    raise CommandError(f"Unknown user_email in memberships: {email}")
                membership, mem_created = OrganizationMembership.objects.update_or_create(
                    user=user,
                    organization=org,
                    defaults={"role": mem_row["role"]},
                )
                action = "Created" if mem_created else "Updated"
                self.stdout.write(f"    {action} membership {email} -> {org.slug} ({membership.role})")

        return projects_by_ref

    def _resolve_project(self, projects_by_ref, org_slug, project_slug):
        ref = (org_slug, project_slug)
        project = projects_by_ref.get(ref)
        if project is None:
            raise CommandError(f"Unknown project ref: {org_slug}/{project_slug}")
        return project

    @transaction.atomic
    def _load_webhook_deliveries(self, deliveries_data, projects_by_ref):
        for row in deliveries_data:
            project = self._resolve_project(
                projects_by_ref,
                row["org_slug"],
                row["project_slug"],
            )
            delivery, created = WebhookDelivery.objects.update_or_create(
                id=uuid.UUID(row["id"]),
                defaults={
                    "project": project,
                    "provider": row["provider"],
                    "delivery_id": row["delivery_id"],
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(
                f"  {action} webhook delivery {delivery.provider}:{delivery.delivery_id}",
            )

    @transaction.atomic
    def _load_build_events(self, events_data, projects_by_ref):
        for row in events_data:
            project = self._resolve_project(
                projects_by_ref,
                row["org_slug"],
                row["project_slug"],
            )
            event, created = BuildEvent.objects.update_or_create(
                id=uuid.UUID(row["id"]),
                defaults={
                    "project": project,
                    "status": row["status"],
                    "branch": row["branch"],
                    "commit_sha": row["commit_sha"],
                    "duration": row.get("duration"),
                    "raw_payload": row["raw_payload"],
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(
                f"  {action} build event {event.status} {event.branch} ({project.slug})",
            )
