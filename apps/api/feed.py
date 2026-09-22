from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.feed.models import FeedConversation, FeedMessage, Post, PostInterest, PostLike
from apps.notifications.models import Notification, notify
from apps.safety.models import Block

from .pagination import TenPerPagePagination


def _post_payload(post, user):
    liked = PostLike.objects.filter(post=post, user=user).exists()
    my_interest = PostInterest.objects.filter(post=post, requester=user).first()
    conversation_id = None
    if my_interest and my_interest.status == PostInterest.STATUS_ACCEPTED:
        conversation_id = getattr(my_interest, "conversation", None) and my_interest.conversation.id

    return {
        "id": post.id,
        "author_id": post.author_id,
        "author_name": post.author.get_full_name() or post.author.username,
        "author_avatar_url": post.author.avatar.url if post.author.avatar else None,
        "caption": post.caption,
        "city": post.city.name if post.city_id else None,
        "place": post.place.name if post.place_id else None,
        "mood": post.mood.name if post.mood_id else None,
        "date_value": post.date_value,
        "time_value": post.time_value,
        "cover_image": post.cover_image_url,
        "created_at": post.created_at,
        "like_count": post.likes.count(),
        "liked_by_me": liked,
        "is_mine": post.author_id == user.id,
        "my_interest_status": my_interest.status if my_interest else None,
        "conversation_id": conversation_id,
    }


class FeedListView(APIView):
    """
    GET /api/feed/?page=1 — fil public paginé (10/page) des idées de sortie
    actives. Pas de temps réel poussé par le serveur (pas de WebSocket, pas
    de polling automatique) pour ne pas solliciter le serveur en continu :
    un nouveau post qu'on vient de publier soi-même est ajouté tout de
    suite côté client, les posts des autres apparaissent à l'actualisation
    ou en cliquant « Voir plus ».
    """

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TenPerPagePagination

    def get(self, request):
        blocked_ids = set(Block.objects.filter(user=request.user).values_list("blocked_user_id", flat=True))
        blocked_by_ids = set(Block.objects.filter(blocked_user=request.user).values_list("user_id", flat=True))
        qs = Post.objects.filter(is_active=True).exclude(
            author_id__in=blocked_ids | blocked_by_ids,
        ).select_related("author", "city", "place", "mood")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request)
        data = [_post_payload(p, request.user) for p in page]
        return paginator.get_paginated_response(data)

    def post(self, request):
        """POST /api/feed/ — publier une nouvelle idée de sortie."""
        caption = (request.data.get("caption") or "").strip()
        if not caption:
            return Response({"detail": "Écris un petit message pour ton idée de sortie."}, status=status.HTTP_400_BAD_REQUEST)

        date_value = request.data.get("date_value") or None
        if date_value:
            try:
                parsed_date = timezone.datetime.strptime(str(date_value), "%Y-%m-%d").date()
                if parsed_date <= timezone.localdate():
                    return Response({"detail": "La date de publication doit être prévue dans le futur."}, status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return Response({"detail": "Date invalide."}, status=status.HTTP_400_BAD_REQUEST)

        post = Post.objects.create(
            author=request.user,
            caption=caption[:500],
            city_id=request.data.get("city_id") or None,
            place_id=request.data.get("place_id") or None,
            mood_id=request.data.get("mood_id") or None,
            date_value=parsed_date if date_value else None,
            time_value=request.data.get("time_value") or None,
            image=request.data.get("image") or None,
        )
        return Response(_post_payload(post, request.user), status=status.HTTP_201_CREATED)


class PostDeactivateView(APIView):
    """POST /api/feed/<id>/close/ — l'auteur·e retire son post (a trouvé quelqu'un, ou changement d'avis)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id, author=request.user)
        post.is_active = False
        post.save(update_fields=["is_active"])
        return Response({"detail": "Post retiré du fil."})


class PostLikeToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        _, created = PostLike.objects.get_or_create(post=post, user=request.user)
        return Response({"liked": True, "like_count": post.likes.count()}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def delete(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        PostLike.objects.filter(post=post, user=request.user).delete()
        return Response({"liked": False, "like_count": post.likes.count()})


class PostInterestCreateView(APIView):
    """
    POST /api/feed/<id>/interest/ body: {"message": "..."}
    Envoie (ou renvoie, si une précédente demande a été déclinée) une
    demande pour discuter — ne crée PAS de conversation directement :
    voir PostInterestRespondView pour l'acceptation par l'auteur·e.
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "invitation-respond"

    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        if post.author_id == request.user.id:
            return Response({"detail": "C'est ton propre post."}, status=status.HTTP_400_BAD_REQUEST)

        if Block.objects.filter(user=post.author, blocked_user=request.user).exists() or \
           Block.objects.filter(user=request.user, blocked_user=post.author).exists():
            return Response({"detail": "Impossible d'envoyer une demande à cette personne."}, status=status.HTTP_403_FORBIDDEN)

        interest, created = PostInterest.objects.get_or_create(
            post=post, requester=request.user,
            defaults={"message": request.data.get("message", "")[:300]},
        )
        if not created:
            if interest.status == PostInterest.STATUS_DECLINED:
                interest.status = PostInterest.STATUS_PENDING
                interest.message = request.data.get("message", "")[:300]
                interest.responded_at = None
                interest.save(update_fields=["status", "message", "responded_at"])
            elif interest.status == PostInterest.STATUS_ACCEPTED:
                return Response({"detail": "Vous discutez déjà ensemble !"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"detail": "Ta demande est déjà en attente de réponse."}, status=status.HTTP_400_BAD_REQUEST)

        notify(
            post.author,
            Notification.TYPE_SYSTEM,
            "Nouvelle demande sur ton post",
            message=f"{request.user.get_full_name() or request.user.username} aimerait discuter de ta sortie.",
            link="/messages/demandes/",
        )
        return Response({"detail": "Demande envoyée !", "status": interest.status}, status=status.HTTP_201_CREATED)


class MyReceivedInterestsView(APIView):
    """GET /api/feed/demandes-recues/ — demandes en attente sur mes posts, à accepter/décliner."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        interests = PostInterest.objects.filter(
            post__author=request.user, status=PostInterest.STATUS_PENDING,
        ).select_related("requester", "post").order_by("-created_at")
        data = [{
            "id": i.id,
            "post_id": i.post_id,
            "post_caption": i.post.caption,
            "requester_id": i.requester_id,
            "requester_name": i.requester.get_full_name() or i.requester.username,
            "message": i.message,
            "created_at": i.created_at,
        } for i in interests]
        return Response(data)


class PostInterestRespondView(APIView):
    """POST /api/feed/demandes/<id>/repondre/ body: {"response": "accept"|"decline"}"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, interest_id):
        interest = get_object_or_404(
            PostInterest, pk=interest_id, post__author=request.user, status=PostInterest.STATUS_PENDING,
        )
        response = request.data.get("response")
        if response not in ("accept", "decline"):
            return Response({"detail": "Réponse invalide."}, status=status.HTTP_400_BAD_REQUEST)

        interest.status = PostInterest.STATUS_ACCEPTED if response == "accept" else PostInterest.STATUS_DECLINED
        interest.responded_at = timezone.now()
        interest.save(update_fields=["status", "responded_at"])

        if response == "accept":
            conversation = FeedConversation.objects.create(
                interest=interest, post=interest.post,
                author=interest.post.author, requester=interest.requester,
            )
            notify(
                interest.requester,
                Notification.TYPE_INVITATION_ACCEPTED,
                "Ta demande a été acceptée !",
                message=f"{request.user.get_full_name() or request.user.username} a accepté d'en discuter avec toi.",
                link=f"/messages/{conversation.id}/",
            )
            return Response({"detail": "Demande acceptée.", "conversation_id": conversation.id})

        return Response({"detail": "Demande déclinée."})


class FeedConversationMessagesView(APIView):
    """GET/POST /api/feed/conversations/<id>/messages/"""

    permission_classes = [permissions.IsAuthenticated]

    def _get_conversation(self, request, conversation_id):
        conversation = get_object_or_404(FeedConversation, pk=conversation_id)
        if request.user.id not in (conversation.author_id, conversation.requester_id):
            return None
        return conversation

    def get(self, request, conversation_id):
        conversation = self._get_conversation(request, conversation_id)
        if conversation is None:
            return Response({"detail": "Accès non autorisé."}, status=status.HTTP_403_FORBIDDEN)

        conversation.messages.exclude(sender=request.user).update(is_read=True)
        other = conversation.other_party(request.user)
        messages = [{
            "id": m.id,
            "content": m.content,
            "mine": m.sender_id == request.user.id,
            "sender_label": m.sender.get_full_name() or m.sender.username,
            "created_at": m.created_at,
            "is_read": m.is_read,
        } for m in conversation.messages.select_related("sender")]

        return Response({
            "messages": messages,
            "other_party": {
                "id": other.id,
                "name": other.get_full_name() or other.username,
                "avatar_url": other.avatar.url if other.avatar else None,
            },
            "post_caption": conversation.post.caption,
        })

    def post(self, request, conversation_id):
        conversation = self._get_conversation(request, conversation_id)
        if conversation is None:
            return Response({"detail": "Accès non autorisé."}, status=status.HTTP_403_FORBIDDEN)

        other = conversation.other_party(request.user)
        if Block.objects.filter(user=request.user, blocked_user=other).exists() or \
           Block.objects.filter(user=other, blocked_user=request.user).exists():
            return Response({"detail": "Impossible d'envoyer un message à cette personne."}, status=status.HTTP_403_FORBIDDEN)

        content = (request.data.get("content") or "").strip()
        if not content:
            return Response({"detail": "Message vide."}, status=status.HTTP_400_BAD_REQUEST)

        FeedMessage.objects.create(conversation=conversation, sender=request.user, content=content[:2000])
        notify(
            other,
            Notification.TYPE_SYSTEM,
            f"Nouveau message de {request.user.get_full_name() or request.user.username}",
            message=content[:100],
            link=f"/messages/{conversation.id}/",
        )
        return Response({"detail": "Message envoyé."}, status=status.HTTP_201_CREATED)


class InboxView(APIView):
    """
    GET /api/messages/ — boîte de réception unifiée : rassemble les
    conversations d'invitations privées (apps.chat) ET celles nées d'un
    post public (apps.feed), triées par dernier message, avec pour
    chacune un badge clair "Rendez-vous proposé" / "Rendez-vous partagé".
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from apps.chat.models import Conversation as DateConversation
        from apps.invitations.models import Invitation

        user = request.user
        items = []

        # --- Conversations d'invitations privées ---------------------------
        date_convs = DateConversation.objects.filter(
            models_q_creator_or_partner(user)
        ).select_related("date_plan", "date_plan__creator", "date_plan__place", "date_plan__invitation")

        for conv in date_convs:
            plan = conv.date_plan
            is_author = plan.creator_id == user.id
            invitation = getattr(plan, "invitation", None)
            other_name = None
            other_avatar_url = None
            if is_author and invitation:
                if invitation.partner_user_id:
                    other_name = invitation.partner_user.get_full_name() or invitation.partner_user.username
                    other_avatar_url = invitation.partner_user.avatar.url if invitation.partner_user.avatar else None
                else:
                    other_name = invitation.partner_name or "Ton/ta partenaire"
            elif not is_author:
                other_name = plan.creator.get_full_name() or plan.creator.username
                other_avatar_url = plan.creator.avatar.url if plan.creator.avatar else None

            last_msg = conv.messages.order_by("-created_at").first()
            unread = conv.messages.filter(is_read=False).exclude(from_creator=is_author).count()
            items.append({
                "kind": "date",
                "id": plan.id,
                "url": f"/dates/{plan.id}/chat/" if is_author else f"/invite/{invitation.token}/chat/" if invitation else None,
                "label": "Rendez-vous proposé" if is_author else "Rendez-vous partagé",
                "title": plan.place.name if plan.place_id else (plan.activity.name if plan.activity_id else "Rendez-vous"),
                "other_name": other_name,
                "other_avatar_url": other_avatar_url,
                "last_message": last_msg.content if last_msg else None,
                "last_at": last_msg.created_at if last_msg else conv.created_at,
                "unread": unread,
            })

        # --- Conversations nées du fil public -------------------------------
        feed_convs = FeedConversation.objects.filter(
            models_q_author_or_requester(user)
        ).select_related("post", "author", "requester")

        for conv in feed_convs:
            is_author = conv.author_id == user.id
            other = conv.requester if is_author else conv.author
            last_msg = conv.messages.order_by("-created_at").first()
            unread = conv.messages.filter(is_read=False).exclude(sender=user).count()
            items.append({
                "kind": "feed",
                "id": conv.id,
                "url": f"/messages/{conv.id}/",
                "label": "Rendez-vous proposé" if is_author else "Rendez-vous partagé",
                "title": conv.post.caption[:60],
                "other_name": other.get_full_name() or other.username,
                "other_avatar_url": other.avatar.url if other.avatar else None,
                "last_message": last_msg.content if last_msg else None,
                "last_at": last_msg.created_at if last_msg else conv.created_at,
                "unread": unread,
            })

        items.sort(key=lambda i: i["last_at"], reverse=True)
        return Response(items)


def models_q_creator_or_partner(user):
    from django.db.models import Q
    return Q(date_plan__creator=user) | Q(date_plan__invitation__partner_user=user)


def models_q_author_or_requester(user):
    from django.db.models import Q
    return Q(author=user) | Q(requester=user)
