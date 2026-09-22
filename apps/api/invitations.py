from django.shortcuts import get_object_or_404
from django.core.exceptions import DisallowedHost
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import SiteConfiguration
from apps.invitations.models import Invitation
from apps.planner.models import DatePlan

from .invitation_serializers import InvitationPublicSerializer, InvitationSerializer


def _absolute_media_url(request, file_field):
    """URL absolue d'un ImageField, ou None si le champ est vide — évite de
    dupliquer ce garde-fou dans chaque vue qui expose une image de lieu/activité."""
    if not file_field:
        return None
    try:
        return request.build_absolute_uri(file_field.url)
    except (ValueError, DisallowedHost):
        return None


class InvitationCreateView(APIView):
    """
    POST /api/invitations/create/   body: {"date_plan": <id>}
    Génère (ou renvoie si elle existe déjà) l'invitation à partager.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_verified:
            return Response(
                {"detail": "Confirme ton adresse e-mail avant de partager un rendez-vous."},
                status=status.HTTP_403_FORBIDDEN,
            )

        plan_id = request.data.get("date_plan")
        plan = DatePlan.objects.filter(pk=plan_id, creator=request.user).first()
        if plan is None:
            return Response({"detail": "Rendez-vous introuvable."}, status=status.HTTP_404_NOT_FOUND)
        if plan.status != DatePlan.STATUS_COMPLETED:
            return Response(
                {"detail": "Termine d'abord la construction du rendez-vous."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invitation = getattr(plan, "invitation", None)
        created = False
        if invitation is None:
            config = SiteConfiguration.load()
            invitation = Invitation.objects.create(
                date_plan=plan,
                expires_at=timezone.now() + timezone.timedelta(days=config.invitation_expiration_days),
            )
            created = True

        serializer_request = request
        try:
            request.get_host()
        except DisallowedHost:
            # DRF ImageFields also build absolute URLs when a request is in
            # the serializer context. Relative media/share URLs are safer
            # than turning a completed rendez-vous into a 500 response.
            serializer_request = None
        serializer = InvitationSerializer(invitation, context={"request": serializer_request})
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class InvitationDetailView(APIView):
    """GET /api/invitations/<token>/ — état vu par le CRÉATEUR (données complètes)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, token):
        invitation = get_object_or_404(Invitation, token=token, date_plan__creator=request.user)
        return Response(InvitationSerializer(invitation, context={"request": request}).data)


class InvitationCancelView(APIView):
    """POST /api/invitations/<token>/cancel/ — le créateur annule l'invitation."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, token):
        invitation = get_object_or_404(Invitation, token=token, date_plan__creator=request.user)
        invitation.status = Invitation.STATUS_CANCELLED
        invitation.save(update_fields=["status"])
        return Response(InvitationSerializer(invitation, context={"request": request}).data)


class InvitationPublicView(APIView):
    """
    GET /api/invitations/<token>/public/ — vue partenaire.

    Sécurité : depuis la refonte, quiconque reçoit un lien ou un QR code
    doit obligatoirement avoir un compte Date With U pour consulter le
    contenu (voir aussi `core.views.invitation_public_view`, qui affiche un
    mur d'inscription côté HTML avant même que ce endpoint ne soit appelé).
    `IsAuthenticated` fait donc office de deuxième verrou, y compris pour
    quelqu'un qui appellerait directement l'API sans passer par la page.
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "invitation-public"

    def get(self, request, token):
        invitation = get_object_or_404(Invitation, token=token)
        is_owner = request.user.is_authenticated and request.user.id == invitation.date_plan.creator_id
        if invitation.is_expired and invitation.status not in (
            Invitation.STATUS_ACCEPTED, Invitation.STATUS_MAYBE, Invitation.STATUS_DECLINED,
        ):
            invitation.status = Invitation.STATUS_EXPIRED
            invitation.save(update_fields=["status"])
        elif not is_owner:
            # Le créateur qui ouvre son propre lien (pour vérifier le rendu,
            # le repartager...) ne doit pas compter comme une "vue" par le
            # ou la partenaire, ni se notifier lui-même.
            invitation.mark_viewed()
        return Response(InvitationPublicSerializer(invitation, context={"request": request}).data)


class InvitationRespondView(APIView):
    """
    POST /api/invitations/<token>/respond/
        body: {"response": "accept"|"maybe"|"decline", "partner_name": "...", "message": "..."}

    Réservé aux utilisateurs connectés — voir `InvitationPublicView`.
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "invitation-respond"

    def post(self, request, token):
        invitation = get_object_or_404(Invitation, token=token)

        if request.user.is_authenticated and request.user.id == invitation.date_plan.creator_id:
            # Bug corrigé : rien n'empêchait auparavant la personne à
            # l'origine du rendez-vous d'accepter/décliner sa propre
            # proposition (en ouvrant son propre lien de partage, par
            # exemple). On bloque explicitement côté serveur, quel que
            # soit ce que ferait ou non l'interface.
            return Response(
                {"detail": "Tu ne peux pas répondre à ta propre invitation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if invitation.is_expired:
            return Response({"detail": "Cette invitation a expiré."}, status=status.HTTP_400_BAD_REQUEST)

        from apps.safety.models import Block
        creator = invitation.date_plan.creator
        if Block.objects.filter(user=creator, blocked_user=request.user).exists() or \
           Block.objects.filter(user=request.user, blocked_user=creator).exists():
            # L'un des deux a bloqué l'autre : on n'affiche pas de détail
            # explicite (ne pas révéler qu'on a été bloqué), juste un refus.
            return Response({"detail": "Impossible de répondre à cette invitation."}, status=status.HTTP_403_FORBIDDEN)

        response_value = request.data.get("response")
        if response_value not in ("accept", "maybe", "decline"):
            return Response(
                {"detail": "La réponse doit être 'accept', 'maybe' ou 'decline'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        partner_user = request.user if request.user.is_authenticated else None
        invitation.respond(
            response_value,
            partner_name=request.data.get("partner_name", ""),
            partner_user=partner_user,
            message=request.data.get("message", ""),
        )
        return Response(InvitationPublicSerializer(invitation).data)


class MyDatesListView(APIView):
    """
    GET /api/my-dates/?when=upcoming|past — tableau de bord « mes rendez-vous ».
    Sans `when`, renvoie tout (historique complet, Phase 5).
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        plans = (
            DatePlan.objects.filter(creator=request.user, status=DatePlan.STATUS_COMPLETED)
            .select_related("invitation", "city", "place", "activity", "mood")
            .order_by("-date_value", "-updated_at")
        )

        when = request.query_params.get("when")
        if when in ("upcoming", "past"):
            today = timezone.now().date()
            if when == "upcoming":
                plans = plans.filter(date_value__gte=today)
            else:
                plans = plans.filter(date_value__lt=today)

        data = []
        for plan in plans:
            invitation = getattr(plan, "invitation", None)
            data.append({
                "plan_id": plan.id,
                "date_value": plan.date_value,
                "time_value": plan.time_value,
                "city": plan.city.name if plan.city else None,
                "place": plan.place.name if plan.place else None,
                "place_image": _absolute_media_url(request, plan.place.main_image) if plan.place else None,
                "activity": plan.activity.name if plan.activity else None,
                "activity_image": _absolute_media_url(request, plan.activity.image) if plan.activity else None,
                "mood": plan.mood.name if plan.mood else None,
                "invitation_status": invitation.status if invitation else None,
                "invitation_token": invitation.token if invitation else None,
            })
        return Response(data)


class ReceivedInvitationsListView(APIView):
    """
    GET /api/my-dates/received/
    Les invitations reçues par l'utilisateur connecté (il/elle est
    `partner_user` sur l'invitation) — complète `MyDatesListView` qui, elle,
    ne renvoie que ce que l'utilisateur a lui-même CRÉÉ. Voir la page
    « Tous mes rendez-vous », qui distingue clairement les deux (section
    demandée : ne pas mélanger « proposé » et « invitation reçue »).
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        invitations = (
            Invitation.objects.filter(partner_user=request.user)
            .select_related("date_plan", "date_plan__city", "date_plan__place", "date_plan__activity", "date_plan__mood", "date_plan__creator")
            .order_by("-created_at")
        )
        data = []
        for invitation in invitations:
            plan = invitation.date_plan
            creator = plan.creator
            data.append({
                "plan_id": plan.id,
                "invitation_token": invitation.token,
                "invitation_status": invitation.status,
                "creator_id": creator.id,
                "creator_name": creator.get_full_name() or creator.username,
                "date_value": plan.date_value,
                "time_value": plan.time_value,
                "city": plan.city.name if plan.city else None,
                "place": plan.place.name if plan.place else None,
                "place_image": _absolute_media_url(request, plan.place.main_image) if plan.place else None,
                "activity": plan.activity.name if plan.activity else None,
                "activity_image": _absolute_media_url(request, plan.activity.image) if plan.activity else None,
                "mood": plan.mood.name if plan.mood else None,
            })
        return Response(data)


class MyDateDetailView(APIView):
    """GET /api/my-dates/<plan_id>/ — détail complet d'un rendez-vous (historique)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, plan_id):
        plan = DatePlan.objects.filter(pk=plan_id, creator=request.user).first()
        if plan is None:
            return Response({"detail": "Introuvable."}, status=status.HTTP_404_NOT_FOUND)

        from .serializers import DatePlanStateSerializer
        payload = DatePlanStateSerializer(plan).data
        invitation = getattr(plan, "invitation", None)
        if invitation is not None:
            payload["invitation"] = InvitationSerializer(invitation, context={"request": request}).data
        return Response(payload)
