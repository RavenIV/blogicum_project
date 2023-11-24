from django.contrib.auth.forms import UserCreationForm


class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        fields = ('username', 'first_name', 'last_name', 'email')
