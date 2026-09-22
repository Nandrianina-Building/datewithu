from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.models import Conversation, Message
from apps.notifications.models import Notification, notify
from apps.planner.models import DatePlan


def _resolve_viewer(request, plan):
    """
    Détermine qui consulte la conversation :
      - le créateur, s'il est authentifié et propriétaire du DatePlan
      - le/la partenaire, via le token de l'invitation — mais un compte
        Date With U (connecté) est désormais obligatoire dans les deux cas :
        un lien ou un QR code partagé ne donne plus accès anonymement.
    Renvoie (is_creator: bool, label: str) ou (None, None) si non autorisé.
    """
    if not request.user.is_authenticated:
        return None, None

    if plan.creator_id == request.user.id:
        return True, request.user.get_full_name() or request.user.username

    token = request.query_params.get("token") or request.data.get("token")
    invitation = getattr(plan, "invitation", None)
    if token and invitation and str(invitation.token) == str(token):
        label = (
            request.query_params.get("partner_name")
            or request.data.get("partner_name")
            or request.user.get_full_name()
            or invitation.partner_name
            or request.user.username
        )
        return False, label

    return None, None


class ChatMessagesView(APIView):
    """
    GET  /api/chat/<date_plan_id>/messages/?token=...         → historique
    POST /api/chat/<date_plan_id>/messages/  body: {content, token?, partner_name?}
    """

    permission_classes = [permissions.IsAuthenticated]  # + vérif fine via _resolve_viewer

    def get(self, request, date_plan_id):
        plan = get_object_or_404(DatePlan, pk=date_plan_id)
        is_creator, label = _resolve_viewer(request, plan)
        if is_creator is None:
            return Response({"detail": "Accès non autorisé à cette conversation."}, status=status.HTTP_403_FORBIDDEN)

        conversation, _ = Conversation.objects.get_or_create(date_plan=plan)

        # Marque comme lus les messages envoyés par l'AUTRE partie.
        conversation.messages.filter(from_creator=(not is_creator), is_read=False).update(is_read=True)

        messages = conversation.messages.all()
        data = [
            {
                "id": m.id,
                "content": m.content,
                "sender_label": m.sender_label,
                "mine": m.from_creator == is_creator,
                "created_at": m.created_at,
                "is_read": m.is_read,
            }
            for m in messages
        ]

        # Identité des deux parties, pour un vrai en-tête de chat (nom du
        # correspondant selon le compte connecté) + un lien "voir son profil".
        # Le créateur a toujours un compte ; le/la partenaire peut ne pas
        # avoir répondu avec un compte lié (invitation.partner_user est
        # alors vide et aucun lien de profil n'est proposé pour lui/elle).
        invitation = getattr(plan, "invitation", None)
        creator_info = {
            "id": plan.creator_id,
            "name": plan.creator.get_full_name() or plan.creator.username,
            "avatar_url": plan.creator.avatar.url if plan.creator.avatar else None,
        }
        partner_user = invitation.partner_user if invitation else None
        partner_info = {
            "id": partner_user.id if partner_user else None,
            "name": (
                (partner_user.get_full_name() or partner_user.username) if partner_user
                else (invitation.partner_name if invitation and invitation.partner_name else "Ton/ta partenaire")
            ),
            "avatar_url": partner_user.avatar.url if partner_user and partner_user.avatar else None,
        }
        other_party = partner_info if is_creator else creator_info

        return Response({
            "conversation_id": conversation.id,
            "messages": data,
            "other_party": other_party,
        })

    def post(self, request, date_plan_id):
        plan = get_object_or_404(DatePlan, pk=date_plan_id)
        is_creator, label = _resolve_viewer(request, plan)
        if is_creator is None:
            return Response({"detail": "Accès non autorisé à cette conversation."}, status=status.HTTP_403_FORBIDDEN)

        from apps.safety.models import Block
        invitation = getattr(plan, "invitation", None)
        other_user = (invitation.partner_user if invitation else None) if is_creator else plan.creator
        if other_user is not None and (
            Block.objects.filter(user=request.user, blocked_user=other_user).exists()
            or Block.objects.filter(user=other_user, blocked_user=request.user).exists()
        ):
            return Response({"detail": "Impossible d'envoyer un message à cette personne."}, status=status.HTTP_403_FORBIDDEN)

        content = (request.data.get("content") or "").strip()
        if not content:
            return Response({"detail": "Message vide."}, status=status.HTTP_400_BAD_REQUEST)

        conversation, _ = Conversation.objects.get_or_create(date_plan=plan)
        message = Message.objects.create(
            conversation=conversation, from_creator=is_creator, sender_label=label, content=content,
        )

        # Le créateur n'a pas forcément de moyen de savoir qu'un message
        # partenaire est arrivé sans notification interne (le/la partenaire,
        # lui/elle, n'a généralement pas de compte pour en recevoir).
        if not is_creator:
            notify(
                plan.creator,
                Notification.TYPE_SYSTEM,
                f"Nouveau message de {label}",
                message=content[:100],
                link=f"/dates/{plan.id}/chat/",
            )

        return Response(
            {
                "id": message.id,
                "content": message.content,
                "sender_label": message.sender_label,
                "mine": True,
                "created_at": message.created_at,
            },
            status=status.HTTP_201_CREATED,
        )
