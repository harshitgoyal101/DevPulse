from django.db import transaction
from rest_framework import serializers

from apps.accounts.models import User

from .models import Organization, OrganizationMembership, Project, Role
from .permissions import get_user_role


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "slug", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class OrganizationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "slug", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def create(self, validated_data):
        user = self.context["request"].user
        with transaction.atomic():
            org = Organization.objects.create(**validated_data)
            OrganizationMembership.objects.create(
                user=user,
                organization=org,
                role=Role.ADMIN,
            )
        return org


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            "id",
            "organization_id",
            "name",
            "slug",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "organization_id", "created_at", "updated_at")

    def validate(self, attrs):
        org_id = self.context.get("org_id")
        if org_id is None and self.instance is not None:
            org_id = self.instance.organization_id
        slug = attrs.get("slug")
        if slug is None and self.instance is not None:
            slug = self.instance.slug
        if org_id and slug:
            qs = Project.objects.filter(organization_id=org_id, slug=slug)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"slug": "A project with this slug already exists in the organization."}
                )
        return attrs


class ProjectDetailSerializer(ProjectSerializer):
    """Project detail; webhook_secret visible only to org admins."""

    webhook_secret = serializers.CharField(read_only=True)

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ("webhook_secret",)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            data.pop("webhook_secret", None)
            return data
        role = get_user_role(request.user, instance.organization_id)
        if role != Role.ADMIN:
            data.pop("webhook_secret", None)
        return data


class OrganizationDetailSerializer(OrganizationSerializer):
    projects = ProjectSerializer(many=True, read_only=True)

    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + ("projects",)


class MembershipSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = ("id", "user_id", "email", "role", "created_at")
        read_only_fields = ("id", "user_id", "email", "created_at")


class MembershipCreateSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = OrganizationMembership
        fields = ("id", "user_id", "role", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_user_id(self, value):
        if not User.objects.filter(pk=value).exists():
            raise serializers.ValidationError("User not found.")
        return value

    def validate(self, attrs):
        org_id = self.context["org_id"]
        user_id = attrs["user_id"]
        if OrganizationMembership.objects.filter(
            organization_id=org_id,
            user_id=user_id,
        ).exists():
            raise serializers.ValidationError(
                {"user_id": "User is already a member of this organization."}
            )
        return attrs

    def create(self, validated_data):
        user_id = validated_data.pop("user_id")
        org_id = self.context["org_id"]
        return OrganizationMembership.objects.create(
            user_id=user_id,
            organization_id=org_id,
            **validated_data,
        )


class MembershipUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationMembership
        fields = ("role",)
