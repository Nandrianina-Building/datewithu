from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import FeedConversation


@login_required
def feed_view(request):
    """« Publier une idée de sortie » — fil public façon Instagram."""
    return render(request, "feed/feed.html")


@login_required
def feed_conversation_view(request, conversation_id):
    """Chat d'une conversation née d'un post public (demande acceptée)."""
    conversation = get_object_or_404(FeedConversation, pk=conversation_id)
    if request.user.id not in (conversation.author_id, conversation.requester_id):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Accès non autorisé.")
    return render(request, "feed/conversation.html", {"conversation_id": conversation.id})


@login_required
def inbox_view(request):
    """Page « Messages » unifiée (invitations privées + fil public), façon
    liste de conversations WhatsApp/Messenger."""
    return render(request, "feed/inbox.html")


@login_required
def received_requests_view(request):
    """Demandes de discussion reçues sur mes posts, à accepter/décliner."""
    return render(request, "feed/received_requests.html")
