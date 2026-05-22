"""Celery application for DevPulse async workers."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("devpulse")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
