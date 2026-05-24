"""Celery tasks for webhook ingestion."""

import logging

from celery import shared_task

from apps.ingestion.models import BuildEvent, WebhookDelivery
from apps.ingestion.parsers import parse_webhook_payload

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_webhook_delivery(self, delivery_id: str) -> None:
    try:
        delivery = WebhookDelivery.objects.select_related("project").get(pk=delivery_id)
    except WebhookDelivery.DoesNotExist:
        logger.warning("WebhookDelivery %s not found", delivery_id)
        return

    if BuildEvent.objects.filter(webhook_delivery=delivery).exists():
        return

    parsed = parse_webhook_payload(delivery.provider, delivery.raw_payload)
    if parsed is None:
        logger.info(
            "Skipping unparseable webhook delivery %s (%s)",
            delivery_id,
            delivery.provider,
        )
        return

    BuildEvent.objects.create(
        webhook_delivery=delivery,
        project=delivery.project,
        status=parsed.status,
        branch=parsed.branch,
        commit_sha=parsed.commit_sha,
        duration=parsed.duration,
        raw_payload=delivery.raw_payload,
    )
