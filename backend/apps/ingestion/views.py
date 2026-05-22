"""Public webhook receiver (signature-gated, no JWT)."""

import json
import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ingestion.models import WebhookDelivery, WebhookProvider
from apps.ingestion.signature import verify_github_signature, verify_gitlab_token
from apps.ingestion.tasks import process_webhook_delivery
from apps.organizations.models import Project

logger = logging.getLogger(__name__)

PROVIDER_CHOICES = {WebhookProvider.GITHUB, WebhookProvider.GITLAB}


class WebhookReceiveView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request, provider: str, project_id):
        if provider not in PROVIDER_CHOICES:
            return Response({"detail": "Unknown provider."}, status=status.HTTP_404_NOT_FOUND)

        project = get_object_or_404(Project, pk=project_id)
        body = request.body

        if provider == WebhookProvider.GITHUB:
            if not verify_github_signature(
                project.webhook_secret,
                body,
                request.headers.get("X-Hub-Signature-256"),
            ):
                return Response({"detail": "Invalid signature."}, status=status.HTTP_401_UNAUTHORIZED)
            delivery_id = request.headers.get("X-GitHub-Delivery")
        else:
            if not verify_gitlab_token(
                project.webhook_secret,
                request.headers.get("X-Gitlab-Token"),
            ):
                return Response({"detail": "Invalid signature."}, status=status.HTTP_401_UNAUTHORIZED)
            delivery_id = request.headers.get("X-Gitlab-Event-UUID")

        if not delivery_id:
            return Response(
                {"detail": "Missing delivery identifier header."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            return Response({"detail": "Invalid JSON body."}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(payload, dict):
            return Response({"detail": "JSON body must be an object."}, status=status.HTTP_400_BAD_REQUEST)

        delivery, created = WebhookDelivery.objects.get_or_create(
            provider=provider,
            delivery_id=delivery_id,
            defaults={
                "project": project,
                "raw_payload": payload,
            },
        )

        if created:
            process_webhook_delivery.delay(str(delivery.id))
        else:
            logger.debug(
                "Duplicate webhook delivery %s:%s (project=%s)",
                provider,
                delivery_id,
                delivery.project_id,
            )

        return Response(status=status.HTTP_202_ACCEPTED)
