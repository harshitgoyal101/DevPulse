from django.urls import path

from .views import WebhookReceiveView

urlpatterns = [
    path(
        "<str:provider>/<uuid:project_id>/",
        WebhookReceiveView.as_view(),
        name="webhook-receive",
    ),
]
