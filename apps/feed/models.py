from django.conf import settings
from django.db import models


class Post(models.Model):
    """
    « Publier une idée de sortie » — un post PUBLIC (façon fil Instagram),
    à distinguer de l'invitation privée (apps.invitations) qui vise une
    personne précise via un lien secret. N'importe quel utilisateur peut
    voir un post, le liker, et demander à en discuter (voir `PostInterest`
    — la demande doit être acceptée par l'auteur·e avant que le chat ne
    s'ouvre, pour rester cohérent avec le reste de l'app : personne ne peut
    forcer une conversation).
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Auteur·e",
        related_name="feed_posts", on_delete=models.CASCADE,
    )
    caption = models.TextField("Message", max_length=500)
    city = models.ForeignKey(
        "locations.City", verbose_name="Ville", null=True, blank=True,
        related_name="feed_posts", on_delete=models.SET_NULL,
    )
    place = models.ForeignKey(
        "catalog.Place", verbose_name="Lieu", null=True, blank=True,
        related_name="feed_posts", on_delete=models.SET_NULL,
    )
    mood = models.ForeignKey(
        "moods.Mood", verbose_name="Ambiance", null=True, blank=True,
        related_name="feed_posts", on_delete=models.SET_NULL,
    )
    date_value = models.DateField("Date envisagée", null=True, blank=True)
    time_value = models.TimeField("Heure envisagée", null=True, blank=True)
    image = models.ImageField(
        "Photo", upload_to="feed/posts/%Y/%m/", null=True, blank=True,
        help_text="Photo optionnelle jointe à la publication.",
    )

    is_active = models.BooleanField(
        "Actif", default=True,
        help_text="Décoché automatiquement une fois que l'auteur·e a trouvé quelqu'un (ou manuellement).",
    )
    created_at = models.DateTimeField("Publié le", auto_now_add=True)

    class Meta:
        verbose_name = "Post"
        verbose_name_plural = "Posts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author} — {self.caption[:40]}"

    @property
    def cover_image_url(self):
        if self.image:
            return self.image.url
        if self.place_id and self.place.main_image:
            return self.place.main_image.url
        return None


class PostLike(models.Model):
    post = models.ForeignKey(Post, verbose_name="Post", related_name="likes", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Utilisateur",
        related_name="feed_post_likes", on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField("Le", auto_now_add=True)

    class Meta:
        verbose_name = "Like"
        verbose_name_plural = "Likes"
        unique_together = ["post", "user"]


class PostInterest(models.Model):
    """
    Demande « Discuter » envoyée sur un post. Reste `pending` tant que
    l'auteur·e n'a pas répondu — c'est cette acceptation qui crée la
    conversation (`FeedConversation`), jamais l'envoi de la demande seule.
    """

    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_DECLINED = "declined"
    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_ACCEPTED, "Acceptée"),
        (STATUS_DECLINED, "Déclinée"),
    ]

    post = models.ForeignKey(Post, verbose_name="Post", related_name="interests", on_delete=models.CASCADE)
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Demandeur·se",
        related_name="feed_interests_sent", on_delete=models.CASCADE,
    )
    message = models.CharField("Message", max_length=300, blank=True)
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField("Demandé le", auto_now_add=True)
    responded_at = models.DateTimeField("Répondu le", null=True, blank=True)

    class Meta:
        verbose_name = "Demande de discussion"
        verbose_name_plural = "Demandes de discussion"
        unique_together = ["post", "requester"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.requester} → post #{self.post_id} ({self.get_status_display()})"


class FeedConversation(models.Model):
    """Conversation créée automatiquement quand une `PostInterest` est
    acceptée — système de messagerie séparé de `apps.chat` (qui reste
    dédié aux invitations privées), réuni avec lui uniquement au niveau de
    la page « Messages » (voir apps.feed.views.inbox_view)."""

    interest = models.OneToOneField(
        PostInterest, verbose_name="Demande d'origine",
        related_name="conversation", on_delete=models.CASCADE,
    )
    post = models.ForeignKey(Post, verbose_name="Post", related_name="conversations", on_delete=models.CASCADE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Auteur·e du post",
        related_name="feed_conversations_as_author", on_delete=models.CASCADE,
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Demandeur·se",
        related_name="feed_conversations_as_requester", on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField("Créée le", auto_now_add=True)

    class Meta:
        verbose_name = "Conversation (fil public)"
        verbose_name_plural = "Conversations (fil public)"

    def __str__(self):
        return f"{self.author} ↔ {self.requester} — post #{self.post_id}"

    def other_party(self, user):
        return self.requester if user.id == self.author_id else self.author


class FeedMessage(models.Model):
    conversation = models.ForeignKey(
        FeedConversation, verbose_name="Conversation",
        related_name="messages", on_delete=models.CASCADE,
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Expéditeur·rice",
        related_name="feed_messages_sent", on_delete=models.CASCADE,
    )
    content = models.TextField("Contenu")
    is_read = models.BooleanField("Lu", default=False)
    created_at = models.DateTimeField("Envoyé le", auto_now_add=True)

    class Meta:
        verbose_name = "Message (fil public)"
        verbose_name_plural = "Messages (fil public)"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender}: {self.content[:40]}"
