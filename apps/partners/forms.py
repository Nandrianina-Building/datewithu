from django import forms

from apps.catalog.models import Place

from .models import PlaceClaim


class PlaceClaimForm(forms.ModelForm):
    class Meta:
        model = PlaceClaim
        fields = ["role", "proof_details"]
        widgets = {
            "proof_details": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Ex : je suis le gérant, voici mon numéro professionnel affiché sur la fiche...",
            }),
        }


class PlaceEditForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = [
            "short_description", "full_description", "phone", "email",
            "website", "facebook", "instagram",
        ]
        widgets = {
            "short_description": forms.TextInput(),
            "full_description": forms.Textarea(attrs={"rows": 5}),
        }
