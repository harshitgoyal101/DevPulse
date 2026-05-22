"""POST a sample CI webhook to the local API with a valid signature."""

import hashlib
import hmac
import json
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError

from apps.ingestion.models import WebhookProvider
from apps.organizations.models import Project

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"

GITHUB_FIXTURE = FIXTURES_DIR / "github_workflow_run.json"
GITLAB_FIXTURE = FIXTURES_DIR / "gitlab_pipeline.json"


class Command(BaseCommand):
    help = "Send a sample GitHub or GitLab webhook to POST /api/webhooks/{provider}/{project_id}/."

    def add_arguments(self, parser):
        parser.add_argument(
            "--provider",
            choices=[WebhookProvider.GITHUB, WebhookProvider.GITLAB],
            default=WebhookProvider.GITHUB,
        )
        parser.add_argument("--project-id", type=uuid.UUID, help="Target project UUID.")
        parser.add_argument(
            "--org-slug",
            type=str,
            help="Resolve project by org slug + project slug (e.g. acme-corp + web-api).",
        )
        parser.add_argument("--project-slug", type=str, help="Project slug within org.")
        parser.add_argument(
            "--base-url",
            default="http://127.0.0.1:8000",
            help="API base URL (default: http://127.0.0.1:8000).",
        )
        parser.add_argument(
            "--delivery-id",
            default=None,
            help="Provider delivery ID (default: random UUID).",
        )
        parser.add_argument(
            "--fixture",
            type=Path,
            default=None,
            help="JSON payload file (default: built-in fixture per provider).",
        )

    def handle(self, *args, **options):
        provider = options["provider"]
        project = self._resolve_project(options)
        fixture_path = options["fixture"] or (
            GITHUB_FIXTURE if provider == WebhookProvider.GITHUB else GITLAB_FIXTURE
        )
        if not fixture_path.is_file():
            raise CommandError(f"Fixture not found: {fixture_path}")

        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        body = json.dumps(payload).encode("utf-8")
        delivery_id = options["delivery_id"] or str(uuid.uuid4())

        url = f"{options['base_url'].rstrip('/')}/api/webhooks/{provider}/{project.id}/"
        headers = {"Content-Type": "application/json"}

        if provider == WebhookProvider.GITHUB:
            digest = hmac.new(
                project.webhook_secret.encode("utf-8"),
                body,
                hashlib.sha256,
            ).hexdigest()
            headers["X-Hub-Signature-256"] = f"sha256={digest}"
            headers["X-GitHub-Delivery"] = delivery_id
        else:
            headers["X-Gitlab-Token"] = project.webhook_secret
            headers["X-Gitlab-Event-UUID"] = delivery_id

        request = Request(url, data=body, headers=headers, method="POST")
        self.stdout.write(f"POST {url}")
        self.stdout.write(f"  delivery_id={delivery_id}")

        try:
            with urlopen(request, timeout=30) as response:
                status = response.status
                response_body = response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            status = exc.code
            response_body = exc.read().decode("utf-8", errors="replace")
        except URLError as exc:
            raise CommandError(f"Request failed: {exc}") from exc

        if status == 202:
            self.stdout.write(self.style.SUCCESS(f"Response: {status} Accepted"))
        else:
            self.stdout.write(self.style.ERROR(f"Response: {status} {response_body}"))
            raise CommandError(f"Unexpected status {status}")

    def _resolve_project(self, options) -> Project:
        if options["project_id"]:
            try:
                return Project.objects.select_related("organization").get(pk=options["project_id"])
            except Project.DoesNotExist as exc:
                raise CommandError(f"Project not found: {options['project_id']}") from exc

        org_slug = options["org_slug"]
        project_slug = options["project_slug"]
        if not org_slug or not project_slug:
            raise CommandError("Provide --project-id or both --org-slug and --project-slug.")

        try:
            return Project.objects.select_related("organization").get(
                organization__slug=org_slug,
                slug=project_slug,
            )
        except Project.DoesNotExist as exc:
            raise CommandError(f"Project not found: {org_slug}/{project_slug}") from exc
