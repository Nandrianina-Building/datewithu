from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Notification


class NotificationListView(APIView):
    """
    GET /api/notifications/?unread=1&page=1 — paginé par tranches de 20,
    pour permettre à la page Notifications de charger le reste
    progressivement ("Voir plus") plutôt que de tout récupérer d'un coup
    (l'ancienne version plafonnait arbitrairement à 50 résultats, sans
    aucun moyen d'accéder aux plus anciennes).
    """

    permission_classes = [permissions.IsAuthenticated]
    PAGE_SIZE = 20

    def get(self, request):
        qs = Notification.objects.filter(user=request.user)
        if request.query_params.get("unread"):
            qs = qs.filter(is_read=False)

        try:
            page = max(1, int(request.query_params.get("page", 1)))
        except ValueError:
            page = 1

        total = qs.count()
        start = (page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        page_items = qs[start:end]

        data = [
            {
                "id": n.id,
                "type": n.notif_type,
                "title": n.title,
                "message": n.message,
                "link": n.link,
                "is_read": n.is_read,
                "created_at": n.created_at,
            }
            for n in page_items
        ]
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        has_more = end < total
        return Response({
            "results": data,
            "unread_count": unread_count,
            "page": page,
            "has_more": has_more,
        })


class NotificationDeleteView(APIView):
    """DELETE /api/notifications/<id>/ — supprime une notification."""

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationMarkReadView(APIView):
    """POST /api/notifications/<id>/read/"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response({"id": notification.id, "is_read": True})


class NotificationMarkAllReadView(APIView):
    """POST /api/notifications/read-all/"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"updated": updated}, status=status.HTTP_200_OK)
