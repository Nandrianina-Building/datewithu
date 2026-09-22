from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.safety.models import Block, Report

User = get_user_model()


class BlockToggleView(APIView):
    """
    POST /api/safety/block/<user_id>/   — bloque un utilisateur.
    DELETE /api/safety/block/<user_id>/ — le débloque.

    Bloquer quelqu'un l'empêche de te répondre à une invitation ou de
    t'envoyer un message dans le chat (voir InvitationRespondView et
    ChatMessagesView, qui vérifient `Block` dans les deux sens).
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, user_id):
        if user_id == request.user.id:
            return Response({"detail": "Tu ne peux pas te bloquer toi-même."}, status=status.HTTP_400_BAD_REQUEST)
        other = get_object_or_404(User, pk=user_id)
        Block.objects.get_or_create(user=request.user, blocked_user=other)
        return Response({"blocked": True}, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        Block.objects.filter(user=request.user, blocked_user_id=user_id).delete()
        return Response({"blocked": False}, status=status.HTTP_200_OK)


class MyBlockedUsersListView(APIView):
    """GET /api/safety/blocked/ — liste des comptes que j'ai bloqués (page profil)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        blocks = Block.objects.filter(user=request.user).select_related("blocked_user")
        data = [
            {
                "id": b.blocked_user_id,
                "name": b.blocked_user.get_full_name() or b.blocked_user.username,
                "blocked_at": b.created_at,
            }
            for b in blocks
        ]
        return Response(data)


class ReportUserView(APIView):
    """POST /api/safety/report/<user_id>/  body: {"reason": "...", "details": "..."}"""

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "report-user"

    def post(self, request, user_id):
        if user_id == request.user.id:
            return Response({"detail": "Tu ne peux pas te signaler toi-même."}, status=status.HTTP_400_BAD_REQUEST)
        other = get_object_or_404(User, pk=user_id)
        reason = request.data.get("reason")
        if reason not in dict(Report.REASON_CHOICES):
            return Response({"detail": "Motif de signalement invalide."}, status=status.HTTP_400_BAD_REQUEST)
        Report.objects.create(
            reporter=request.user,
            reported_user=other,
            reason=reason,
            details=request.data.get("details", ""),
        )
        return Response({"detail": "Signalement envoyé — merci, notre équipe va l'examiner."}, status=status.HTTP_201_CREATED)
