"""Unit tests for webhook payload parsers."""

import pytest

from apps.ingestion.models import BuildStatus, WebhookProvider
from apps.ingestion.parsers import parse_webhook_payload


def _github_payload(**workflow_overrides) -> dict:
    workflow_run = {
        "head_branch": "main",
        "head_sha": "a" * 40,
        "status": "completed",
        "conclusion": "success",
        "run_started_at": "2026-05-01T10:00:00Z",
        "updated_at": "2026-05-01T10:05:00Z",
    }
    workflow_run.update(workflow_overrides)
    return {"workflow_run": workflow_run}


def _gitlab_payload(**attrs_overrides) -> dict:
    attrs = {
        "ref": "main",
        "sha": "b" * 40,
        "status": "success",
        "duration": 120,
    }
    attrs.update(attrs_overrides)
    return {"object_attributes": attrs}


class TestGitHubParser:
    def test_completed_success(self):
        parsed = parse_webhook_payload(WebhookProvider.GITHUB, _github_payload())
        assert parsed is not None
        assert parsed.status == BuildStatus.SUCCESS
        assert parsed.branch == "main"
        assert parsed.commit_sha == "a" * 40
        assert parsed.duration == 300

    def test_in_progress_returns_pending(self):
        parsed = parse_webhook_payload(
            WebhookProvider.GITHUB,
            _github_payload(status="in_progress", conclusion=None),
        )
        assert parsed is not None
        assert parsed.status == BuildStatus.PENDING

    def test_queued_returns_pending(self):
        parsed = parse_webhook_payload(
            WebhookProvider.GITHUB,
            _github_payload(status="queued", conclusion=None),
        )
        assert parsed is not None
        assert parsed.status == BuildStatus.PENDING

    @pytest.mark.parametrize(
        ("conclusion", "expected"),
        [
            ("failure", BuildStatus.FAILURE),
            ("cancelled", BuildStatus.CANCELLED),
            ("skipped", BuildStatus.SKIPPED),
            ("timed_out", BuildStatus.FAILURE),
            ("neutral", BuildStatus.SKIPPED),
            ("stale", BuildStatus.SKIPPED),
        ],
    )
    def test_completed_conclusions(self, conclusion, expected):
        parsed = parse_webhook_payload(
            WebhookProvider.GITHUB,
            _github_payload(conclusion=conclusion),
        )
        assert parsed is not None
        assert parsed.status == expected

    def test_missing_workflow_run(self):
        assert parse_webhook_payload(WebhookProvider.GITHUB, {}) is None
        assert parse_webhook_payload(WebhookProvider.GITHUB, {"workflow_run": "bad"}) is None

    def test_missing_branch_or_sha(self):
        assert (
            parse_webhook_payload(
                WebhookProvider.GITHUB,
                _github_payload(head_branch="", head_sha="a" * 40),
            )
            is None
        )
        assert (
            parse_webhook_payload(
                WebhookProvider.GITHUB,
                _github_payload(head_branch="main", head_sha=""),
            )
            is None
        )

    def test_unknown_status_returns_none(self):
        assert (
            parse_webhook_payload(
                WebhookProvider.GITHUB,
                _github_payload(status="weird", conclusion=None),
            )
            is None
        )

    def test_negative_duration_returns_none(self):
        parsed = parse_webhook_payload(
            WebhookProvider.GITHUB,
            _github_payload(
                run_started_at="2026-05-01T10:05:00Z",
                updated_at="2026-05-01T10:00:00Z",
            ),
        )
        assert parsed is not None
        assert parsed.duration is None

    def test_malformed_timestamps_skip_duration(self):
        parsed = parse_webhook_payload(
            WebhookProvider.GITHUB,
            _github_payload(run_started_at="not-a-date", updated_at="also-not-a-date"),
        )
        assert parsed is not None
        assert parsed.duration is None


class TestGitLabParser:
    def test_success_pipeline(self):
        parsed = parse_webhook_payload(WebhookProvider.GITLAB, _gitlab_payload())
        assert parsed is not None
        assert parsed.status == BuildStatus.SUCCESS
        assert parsed.branch == "main"
        assert parsed.commit_sha == "b" * 40
        assert parsed.duration == 120

    def test_running_returns_pending(self):
        parsed = parse_webhook_payload(
            WebhookProvider.GITLAB,
            _gitlab_payload(status="running", duration=None),
        )
        assert parsed is not None
        assert parsed.status == BuildStatus.PENDING

    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            ("failed", BuildStatus.FAILURE),
            ("canceled", BuildStatus.CANCELLED),
            ("cancelled", BuildStatus.CANCELLED),
            ("skipped", BuildStatus.SKIPPED),
            ("waiting_for_resource", BuildStatus.PENDING),
            ("preparing", BuildStatus.PENDING),
        ],
    )
    def test_status_mapping(self, status, expected):
        parsed = parse_webhook_payload(
            WebhookProvider.GITLAB,
            _gitlab_payload(status=status),
        )
        assert parsed is not None
        assert parsed.status == expected

    def test_missing_object_attributes(self):
        assert parse_webhook_payload(WebhookProvider.GITLAB, {}) is None
        assert parse_webhook_payload(WebhookProvider.GITLAB, {"object_attributes": []}) is None

    def test_missing_ref_or_sha(self):
        assert (
            parse_webhook_payload(
                WebhookProvider.GITLAB,
                _gitlab_payload(ref="", sha="b" * 40),
            )
            is None
        )

    def test_invalid_duration_is_ignored(self):
        parsed = parse_webhook_payload(
            WebhookProvider.GITLAB,
            _gitlab_payload(duration="not-a-number"),
        )
        assert parsed is not None
        assert parsed.duration is None

    def test_unknown_status_returns_none(self):
        assert (
            parse_webhook_payload(
                WebhookProvider.GITLAB,
                _gitlab_payload(status="unknown"),
            )
            is None
        )


class TestParseWebhookPayload:
    def test_unknown_provider_returns_none(self):
        assert parse_webhook_payload("bitbucket", _github_payload()) is None
