from django.core.exceptions import DisallowedHost
from rest_framework import serializers

from apps.invitations.models import Invitation

from .serializers import DatePlanStateSerializer


class InvitationSerializer(serializers.ModelSerializer):
    token = serializers.UUIDField(read_only=True)
    plan = DatePlanStateSerializer(source="date_plan", read_only=True)
    share_url = serializers.SerializerMethodField()

    class Meta:
        model = Invitation
        fields = [
            "id", "token", "status", "plan", "share_url",
            "partner_name", "view_count", "created_at", "expires_at", "responded_at",
        ]

    def get_share_url(self, obj):
        request = self.context.get("request")
        path = f"/invite/{obj.token}/"
        if not request:
            return path
        try:
            return request.build_absolute_uri(path)
        except DisallowedHost:
            # A relative URL still works on the current Date With U host and
            # avoids turning link generation into a server error.
            return path


class InvitationPublicSerializer(serializers.ModelSerializer):
    """
    Version exposée au partenaire (non authentifié) : uniquement ce qui est
    nécessaire pour se décider, rien sur l'identité complète du créateur.
    """

    token = serializers.UUIDField(read_only=True)
    plan = DatePlanStateSerializer(source="date_plan", read_only=True)
    creator_name = serializers.SerializerMethodField()
    is_expired = serializers.ReadOnlyField()
    is_own_invitation = serializers.SerializerMethodField()

    class Meta:
        model = Invitation
        fields = ["token", "status", "plan", "creator_name", "expires_at", "is_expired", "is_own_invitation"]

    def get_creator_name(self, obj):
        creator = obj.date_plan.creator
        return creator.get_full_name() or creator.username

    def get_is_own_invitation(self, obj):
        # Empêche la personne qui a créé le rendez-vous de répondre (accepter
        # / décliner) à sa propre proposition si elle ouvre son propre lien —
        # le frontend s'appuie sur ce flag pour afficher un message dédié au
        # lieu du formulaire de réponse (voir InvitationRespondView côté
        # serveur pour le vrai verrou).
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and user.id == obj.date_plan.creator_id)
