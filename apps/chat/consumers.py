"""
Consumer WebSocket pour le chat temps réel.

⚠️ OPTIONNEL — non activé par défaut. Le chat fonctionne déjà en polling
HTTP via apps.api.chat (aucune dépendance supplémentaire). Ce fichier
permet de passer à du vrai temps réel une fois que tu as :

    pip install channels channels-redis daphne

et un serveur Redis disponible. Voir la section "Chat temps réel
(WebSockets)" du README pour le câblage complet (settings.py, asgi.py,
routing.py).
"""
import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.date_plan_id = self.scope["url_route"]["kwargs"]["date_plan_id"]
        self.group_name = f"chat_{self.date_plan_id}"

        authorized, self.is_creator, self.label = await self._authorize()
        if not authorized:
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = (data.get("content") or "").strip()
        if not content:
            return

        message = await self._save_message(content)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "id": message["id"],
                "content": message["content"],
                "sender_label": message["sender_label"],
                "from_creator": message["from_creator"],
                "created_at": message["created_at"],
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "id": event["id"],
            "content": event["content"],
            "sender_label": event["sender_label"],
            "mine": event["from_creator"] == self.is_creator,
            "created_at": event["created_at"],
        }))

    @database_sync_to_async
    def _authorize(self):
        from apps.planner.models import DatePlan

        plan = DatePlan.objects.filter(pk=self.date_plan_id).first()
        if plan is None:
            return False, None, None

        user = self.scope.get("user")
        if user is not None and user.is_authenticated and plan.creator_id == user.id:
            return True, True, user.get_full_name() or user.username

        query_string = self.scope.get("query_string", b"").decode()
        params = dict(p.split("=") for p in query_string.split("&") if "=" in p)
        token = params.get("token")
        invitation = getattr(plan, "invitation", None)
        if token and invitation and str(invitation.token) == token:
            label = params.get("partner_name") or invitation.partner_name or "Partenaire"
            return True, False, label

        return False, None, None

    @database_sync_to_async
    def _save_message(self, content):
        from apps.chat.models import Conversation, Message
        from apps.planner.models import DatePlan

        plan = DatePlan.objects.get(pk=self.date_plan_id)
        conversation, _ = Conversation.objects.get_or_create(date_plan=plan)
        message = Message.objects.create(
            conversation=conversation,
            from_creator=self.is_creator,
            sender_label=self.label,
            content=content,
        )
        return {
            "id": message.id,
            "content": message.content,
            "sender_label": message.sender_label,
            "from_creator": message.from_creator,
            "created_at": message.created_at.isoformat(),
        }
