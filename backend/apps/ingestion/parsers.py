"""Parse provider webhook JSON into normalized build fields."""

from dataclasses import dataclass
from datetime import datetime

from apps.ingestion.models import BuildStatus, WebhookProvider


@dataclass(frozen=True)
class ParsedBuild:
    status: str
    branch: str
    commit_sha: str
    duration: int | None


def _parse_iso_duration_seconds(start: str | None, end: str | None) -> int | None:
    if not start or not end:
        return None
    try:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        delta = end_dt - start_dt
        seconds = int(delta.total_seconds())
        return seconds if seconds >= 0 else None
    except (TypeError, ValueError):
        return None


def _github_workflow_status(workflow_run: dict) -> str | None:
    status = workflow_run.get("status")
    conclusion = workflow_run.get("conclusion")
    if status == "completed":
        mapping = {
            "success": BuildStatus.SUCCESS,
            "failure": BuildStatus.FAILURE,
            "cancelled": BuildStatus.CANCELLED,
            "skipped": BuildStatus.SKIPPED,
            "timed_out": BuildStatus.FAILURE,
            "action_required": BuildStatus.FAILURE,
            "neutral": BuildStatus.SKIPPED,
            "stale": BuildStatus.SKIPPED,
        }
        return mapping.get(conclusion)
    if status in ("queued", "in_progress", "pending", "waiting", "requested"):
        return BuildStatus.PENDING
    return None


def _parse_github(payload: dict) -> ParsedBuild | None:
    workflow_run = payload.get("workflow_run")
    if not isinstance(workflow_run, dict):
        return None

    build_status = _github_workflow_status(workflow_run)
    if build_status is None:
        return None

    branch = workflow_run.get("head_branch") or ""
    commit_sha = workflow_run.get("head_sha") or ""
    if not branch or not commit_sha:
        return None

    duration = _parse_iso_duration_seconds(
        workflow_run.get("run_started_at"),
        workflow_run.get("updated_at"),
    )
    return ParsedBuild(
        status=build_status,
        branch=branch,
        commit_sha=commit_sha,
        duration=duration,
    )


def _gitlab_pipeline_status(attrs: dict) -> str | None:
    status = attrs.get("status")
    mapping = {
        "success": BuildStatus.SUCCESS,
        "failed": BuildStatus.FAILURE,
        "canceled": BuildStatus.CANCELLED,
        "cancelled": BuildStatus.CANCELLED,
        "skipped": BuildStatus.SKIPPED,
        "running": BuildStatus.PENDING,
        "pending": BuildStatus.PENDING,
        "created": BuildStatus.PENDING,
        "waiting_for_resource": BuildStatus.PENDING,
        "preparing": BuildStatus.PENDING,
    }
    return mapping.get(status)


def _parse_gitlab(payload: dict) -> ParsedBuild | None:
    attrs = payload.get("object_attributes")
    if not isinstance(attrs, dict):
        return None

    build_status = _gitlab_pipeline_status(attrs)
    if build_status is None:
        return None

    branch = attrs.get("ref") or ""
    commit_sha = attrs.get("sha") or ""
    if not branch or not commit_sha:
        return None

    duration = attrs.get("duration")
    if duration is not None:
        try:
            duration = int(duration)
        except (TypeError, ValueError):
            duration = None

    return ParsedBuild(
        status=build_status,
        branch=branch,
        commit_sha=commit_sha,
        duration=duration,
    )


def parse_webhook_payload(provider: str, payload: dict) -> ParsedBuild | None:
    if provider == WebhookProvider.GITHUB:
        return _parse_github(payload)
    if provider == WebhookProvider.GITLAB:
        return _parse_gitlab(payload)
    return None
