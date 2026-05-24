from rest_framework import serializers

from apps.ingestion.models import BuildEvent


class BuildEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildEvent
        fields = ("id", "status", "branch", "commit_sha", "duration", "created_at")
        read_only_fields = fields
