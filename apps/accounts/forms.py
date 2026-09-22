from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone

from .models import User


def _no_future_date(value, field_label="Cette date"):
    """Interdit toute date dans le futur (date de naissance, etc.)."""
    if value and value > timezone.localdate():
        raise forms.ValidationError(f"{field_label} ne peut pas être dans le futur.")
    return value


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    website = forms.CharField(
        required=False,
        label="Website",
        widget=forms.TextInput(attrs={
            "autocomplete": "off",
            "tabindex": "-1",
            "aria-hidden": "true",
        }),
    )
    accept_terms = forms.BooleanField(
        required=True,
        label="J'accepte les Conditions Générales d'Utilisation et la Politique de confidentialité",
        error_messages={"required": "Tu dois accepter les CGU pour créer un compte."},
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def clean_website(self):
        value = self.cleaned_data.get("website", "")
        if value:
            raise forms.ValidationError("Inscription invalide.")
        return value

    def save(self, commit=True):
        from django.utils import timezone

        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.accepted_terms_at = timezone.now()
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "email", "phone", "avatar", "bio",
            "birth_date", "email_notifications_enabled",
        ]
        widgets = {
            "birth_date": forms.DateInput(
                attrs={"type": "date", "max": timezone.localdate().isoformat()}, format="%Y-%m-%d",
            ),
            "bio": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_birth_date(self):
        return _no_future_date(self.cleaned_data.get("birth_date"), "La date de naissance")


class CompleteProfileForm(forms.ModelForm):
    """
    Étape obligatoire entre la vérification d'e-mail et le dashboard :
    on ne laisse personne construire de rendez-vous sans un minimum
    d'informations exploitables (prénom/nom pour les invitations,
    téléphone pour être recontacté, date de naissance pour les
    suggestions d'occasions).
    """

    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "avatar", "birth_date"]
        widgets = {
            "birth_date": forms.DateInput(
                attrs={"type": "date", "max": timezone.localdate().isoformat()}, format="%Y-%m-%d",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in User.REQUIRED_PROFILE_FIELDS:
            if name in self.fields:
                self.fields[name].required = True

    def clean_birth_date(self):
        return _no_future_date(self.cleaned_data.get("birth_date"), "La date de naissance")


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Adresse e-mail")


class SetNewPasswordForm(forms.Form):
    new_password1 = forms.CharField(label="Nouveau mot de passe", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Confirme le nouveau mot de passe", widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password1(self):
        password = self.cleaned_data["new_password1"]
        validate_password(password, self.user)
        return password

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("new_password1"), cleaned.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Les deux mots de passe ne correspondent pas.")
        return cleaned

    def save(self):
        self.user.set_password(self.cleaned_data["new_password1"])
        self.user.save(update_fields=["password"])
        return self.user
