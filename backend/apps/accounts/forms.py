from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User


class EmailUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):  # type: ignore[misc]
        model = User


class EmailUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):  # type: ignore[misc]
        model = User
        fields = ("email",)
