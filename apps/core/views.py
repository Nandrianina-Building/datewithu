import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import SiteConfiguration

User = get_user_model()


def terms_view(request):
    return render(request, "core/terms.html", {"config": SiteConfiguration.load()})


def privacy_view(request):
    return render(request, "core/privacy.html", {"config": SiteConfiguration.load()})


def robots_txt_view(request):
    lines = [
        "User-agent: *",
        "Disallow: /accounts/",
        "Disallow: /dashboard/",
        "Disallow: /mes-rendez-vous/",
        "Disallow: /notifications/",
        "Disallow: /invite/",
        "Disallow: /date-builder/",
        "Disallow: /dates/",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def sitemap_xml_view(request):
    """
    Sitemap minimal : uniquement les pages publiques, statiques et sans
    connexion requise — le reste (dashboard, invitations, chat...) n'a
    rien à faire dans un index de moteur de recherche.
    """
    base = f"{request.scheme}://{request.get_host()}"
    urls = [
        (reverse("core:home"), "1.0"),
        (reverse("accounts:register"), "0.5"),
        (reverse("accounts:login"), "0.3"),
        (reverse("core:terms"), "0.2"),
        (reverse("core:privacy"), "0.2"),
    ]
    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, priority in urls:
        xml_parts.append(f"<url><loc>{base}{path}</loc><priority>{priority}</priority></url>")
    xml_parts.append("</urlset>")
    return HttpResponse("\n".join(xml_parts), content_type="application/xml")


def service_worker_view(request):
    """
    Sert le service worker depuis la racine du site (/sw.js) plutôt que
    depuis /static/sw.js : un service worker ne peut contrôler que les
    URLs sous son propre chemin, donc il doit être à la racine pour
    couvrir toute l'app (Phase 8 — PWA).
    """
    path = os.path.join(settings.BASE_DIR, "static", "sw.js")
    with open(path, "rb") as f:
        content = f.read()
    return HttpResponse(content, content_type="application/javascript")


def home_view(request):
    from apps.catalog.models import Place
    from apps.locations.models import City

    config = SiteConfiguration.load()
    cities = City.objects.filter(is_active=True).order_by("display_order", "name")
    cities_total = cities.count()
    cities = cities[:12]
    popular_places = (
        Place.objects.filter(is_active=True)
        .select_related("city", "category")
        .order_by("-is_recommended", "-is_popular", "-rating")[:6]
    )
    return render(
        request,
        "core/home.html",
        {"config": config, "cities": cities, "cities_has_more": cities_total > len(cities), "popular_places": popular_places},
    )


@login_required
def user_dashboard_view(request):
    """
    Tableau de bord utilisateur. Accès conditionné à deux étapes
    obligatoires après l'inscription : avoir cliqué le lien d'activation
    reçu par e-mail, puis avoir complété les infos obligatoires du profil
    (voir apps.accounts.views.verify_pending_view / complete_profile_view).
    """
    if not request.user.is_verified:
        return redirect(f"{reverse('accounts:verify_pending')}?next={request.path}")
    if not request.user.has_completed_profile:
        return redirect(f"{reverse('accounts:complete_profile')}?next={request.path}")
    return render(request, "core/dashboard.html")


@login_required
def date_builder_view(request):
    """
    Page hôte du Date Builder dynamique (Phase 3). Toute la logique
    d'étapes vit côté JS (static/js/date-builder.js) et consomme les
    endpoints /api/date-builder/... en AJAX — cette vue ne fait que
    servir le template.
    """
    return render(
        request,
        "core/date_builder.html",
        {"date_builder_today": timezone.localdate().isoformat()},
    )


@login_required
def map_view(request):
    """Carte interactive des lieux (Phase 8) — Leaflet + OpenStreetMap, pas de clé API requise."""
    return render(request, "core/map.html")


@login_required
def packages_view(request):
    """Rendez-vous clé en main (Phase 8) — alternative rapide au Date Builder."""
    return render(request, "core/packages.html")


@login_required
def all_dates_view(request):
    """
    Vue d'ensemble complète de tous les rendez-vous liés au compte,
    clairement séparés entre ceux que l'utilisateur a proposés et les
    invitations qu'il/elle a reçues d'un·e partenaire (voir
    static/js/all-dates.js et l'API /api/my-dates/ + /api/my-dates/received/).
    """
    return render(request, "core/all_dates.html")


@login_required
def notifications_view(request):
    """
    Page dédiée aux notifications (auparavant seulement un petit widget
    dans le dashboard) : chaque notification est cliquable et amène
    directement vers l'action correspondante (voir `Notification.link`).
    """
    return render(request, "core/notifications.html")


@login_required
def my_dates_page_view(request):
    """
    Page « Tous mes rendez-vous » : rassemble en un seul endroit ce que
    l'utilisateur a PROPOSÉ (rendez-vous qu'il/elle a créés) et ce qu'il/elle
    a REÇU comme invitation d'un·e partenaire — les deux étant clairement
    distingués (section demandée : ne pas mélanger « proposé » et
    « invitation reçue »). Le contenu (images, statut, actions) est chargé
    en AJAX par my-dates-page.js depuis /api/my-dates/ et /api/my-dates/received/.
    """
    return render(request, "core/my_dates.html")


@login_required
def explore_view(request):
    """
    Page de démonstration Phase 5 : parcourir les lieux et les mettre en
    favori (cœur cliquable). Consomme /api/places/ et /api/favorites/.
    """
    return render(request, "core/explore.html")


@login_required
def chat_view(request, plan_id):
    """Chat côté créateur (Phase 7) — authentification par session normale."""
    from apps.planner.models import DatePlan

    plan = get_object_or_404(DatePlan, pk=plan_id, creator=request.user)
    return render(request, "core/chat.html", {
        "date_plan_id": plan.id,
        "token": "",
        "chat_title": "Discussion avec ton/ta partenaire",
    })


@login_required
def chat_public_view(request, token):
    """
    Chat côté partenaire (Phase 7). Un compte Date With U est désormais
    obligatoire pour discuter, même en venant d'un lien/QR d'invitation —
    `@login_required` renvoie vers la connexion/inscription (avec `?next=`)
    si besoin, et `apps.api.chat._resolve_viewer` revérifie ensuite le
    token + l'identité côté API avant de laisser passer un seul message.
    """
    from apps.invitations.models import Invitation

    invitation = get_object_or_404(Invitation, token=token)
    return render(request, "core/chat.html", {
        "date_plan_id": invitation.date_plan_id,
        "token": str(invitation.token),
        "chat_title": f"Discussion avec {invitation.date_plan.creator.get_full_name() or invitation.date_plan.creator.username}",
    })


def invitation_public_view(request, token):
    """
    Page publique d'une invitation (section 98 : balises Open Graph pour un
    bel aperçu WhatsApp/Messenger/Facebook quand le lien — ou le QR code qui
    encode la même URL — est partagé).

    Sécurité : la page reste servie avec un code 200 et ses balises OG pour
    que les robots de prévisualisation (WhatsApp, Messenger, Facebook...)
    continuent de générer un aperçu — ces robots ne s'authentifient jamais
    et n'exécutent aucun JS, donc les rediriger casserait l'aperçu partagé.
    En revanche, pour un VISITEUR humain non connecté, le template
    n'affiche qu'un mur d'inscription/connexion (voir invitation_public.html)
    à la place du contenu réel : aucune donnée du rendez-vous n'est exposée
    tant que la personne n'a pas de compte. Le contenu détaillé n'est de
    toute façon chargé qu'en AJAX via /api/invitations/<token>/public/, qui
    est lui-même protégé par IsAuthenticated (défense en profondeur).
    """
    from apps.invitations.models import Invitation

    invitation = get_object_or_404(Invitation, token=token)
    plan = invitation.date_plan

    og_title = "Tu as reçu une invitation pour un rendez-vous"
    if plan.mood:
        og_title = f"Un rendez-vous {plan.mood.name} t'attend !"

    parts = []
    if plan.place:
        parts.append(plan.place.name)
    elif plan.activity:
        parts.append(plan.activity.name)
    if plan.city:
        parts.append(plan.city.name)
    og_description = " — ".join(parts) or "Découvre les détails de ce rendez-vous sur Date With U."

    og_image = None
    if plan.place and plan.place.main_image:
        og_image = request.build_absolute_uri(plan.place.main_image.url)
    elif plan.activity and plan.activity.image:
        og_image = request.build_absolute_uri(plan.activity.image.url)

    next_url = request.path
    return render(request, "core/invitation_public.html", {
        "token": token,
        "og_title": og_title,
        "og_description": og_description,
        "og_image": og_image,
        "requires_account": not request.user.is_authenticated,
        "register_url": f"{reverse('accounts:register')}?next={next_url}",
        "login_url": f"{reverse('accounts:login')}?next={next_url}",
    })


@login_required
def invitation_qr_view(request, token):
    """
    Renvoie un QR code (PNG) pointant vers la page publique de l'invitation.
    Réservé au créateur du rendez-vous : c'est lui qui imprime/partage le
    QR (section « partage » — lien ET QR code doivent mener au même mur
    d'inscription obligatoire).
    """
    import io

    import qrcode
    from apps.invitations.models import Invitation

    invitation = get_object_or_404(Invitation, token=token, date_plan__creator=request.user)
    url = request.build_absolute_uri(
        reverse("core:invitation_public", kwargs={"token": invitation.token})
    )

    img = qrcode.make(url, box_size=10, border=2)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return HttpResponse(buffer.getvalue(), content_type="image/png")


@login_required
def invitation_card_view(request, token):
    """
    Génère une « carte d'invitation » téléchargeable (PNG) qui combine le
    QR code avec quelques informations visuelles sur le rendez-vous (photo
    du lieu, ville, date, ambiance) — plutôt qu'un QR code nu, difficile à
    identifier une fois enregistré ou imprimé séparément.
    """
    import io

    import qrcode
    from PIL import Image, ImageDraw, ImageFont, ImageOps

    from apps.invitations.models import Invitation

    invitation = get_object_or_404(Invitation, token=token, date_plan__creator=request.user)
    plan = invitation.date_plan
    url = request.build_absolute_uri(
        reverse("core:invitation_public", kwargs={"token": invitation.token})
    )

    W, H = 1080, 1350
    PHOTO_H = 760
    ROSE = (194, 24, 91)
    ROSE_DARK = (140, 15, 65)
    CREAM = (255, 250, 248)
    INK = (35, 30, 35)
    INK_SOFT = (120, 110, 115)

    fonts_dir = os.path.join(settings.BASE_DIR, "static", "fonts")

    def font(name, size):
        return ImageFont.truetype(os.path.join(fonts_dir, name), size)

    f_brand = font("Poppins-Bold.ttf", 38)
    f_title = font("Poppins-Bold.ttf", 58)
    f_meta = font("Poppins-SemiBold.ttf", 32)
    f_caption = font("Poppins-SemiBold.ttf", 30)
    f_small = font("Poppins-Regular.ttf", 24)

    card = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(card)

    # --- Photo (lieu ou activité), ou dégradé de marque à défaut --------
    image_field = None
    if plan.place_id and plan.place.main_image:
        image_field = plan.place.main_image
    elif plan.activity_id and plan.activity.image:
        image_field = plan.activity.image

    photo = None
    if image_field:
        try:
            with image_field.open("rb") as fh:
                photo = Image.open(fh)
                photo.load()
                photo = photo.convert("RGB")
        except Exception:
            photo = None

    if photo is not None:
        photo = ImageOps.fit(photo, (W, PHOTO_H), method=Image.LANCZOS)
    else:
        photo = Image.new("RGB", (W, PHOTO_H), ROSE)
        grad = ImageDraw.Draw(photo)
        for y in range(PHOTO_H):
            t = y / PHOTO_H
            r = int(ROSE[0] * (1 - t) + ROSE_DARK[0] * t)
            g = int(ROSE[1] * (1 - t) + ROSE_DARK[1] * t)
            b = int(ROSE[2] * (1 - t) + ROSE_DARK[2] * t)
            grad.line([(0, y), (W, y)], fill=(r, g, b))

    card.paste(photo, (0, 0))

    # Dégradé sombre en bas de la photo, pour la lisibilité du texte.
    overlay = Image.new("L", (W, PHOTO_H), 0)
    overlay_draw = ImageDraw.Draw(overlay)
    fade_h = 420
    for y in range(fade_h):
        alpha = int(190 * (y / fade_h) ** 1.4)
        overlay_draw.line([(0, PHOTO_H - fade_h + y), (W, PHOTO_H - fade_h + y)], fill=alpha)
    black = Image.new("RGB", (W, PHOTO_H), (0, 0, 0))
    card.paste(black, (0, 0), overlay)

    # --- Pastille "Date With U" en haut ---------------------------------
    # Poppins ne contient pas de glyphes emoji (❤ s'affiche en tofu / carré
    # vide) : on dessine un petit cœur vectoriel à la place plutôt que de
    # compter sur un caractère emoji dans la police.
    def draw_heart(cx, cy, size, color):
        r = size / 4
        draw.ellipse([cx - r * 2, cy - r, cx, cy + r], fill=color)
        draw.ellipse([cx, cy - r, cx + r * 2, cy + r], fill=color)
        draw.polygon([
            (cx - r * 2, cy), (cx + r * 2, cy), (cx, cy + r * 2.6),
        ], fill=color)

    brand_text = "Date With U"
    brand_w = draw.textlength(brand_text, font=f_brand)
    pill_w = brand_w + 110
    draw.rounded_rectangle([(40, 40), (40 + pill_w, 40 + 78)], radius=39, fill="white")
    draw_heart(80, 79, 26, ROSE)
    draw.text((108, 58), brand_text, font=f_brand, fill=ROSE)

    # --- Titre + méta sur la photo ---------------------------------------
    title = plan.place.name if plan.place_id else (plan.activity.name if plan.activity_id else "Un rendez-vous à découvrir")
    if len(title) > 34:
        title = title[:33].rstrip() + "…"
    draw.text((50, PHOTO_H - 200), title, font=f_title, fill="white")

    meta_bits = []
    if plan.city_id:
        meta_bits.append(plan.city.name)
    if plan.date_value:
        meta_bits.append(plan.date_value.strftime("%d/%m/%Y") + (f" à {plan.time_value.strftime('%H:%M')}" if plan.time_value else ""))
    if meta_bits:
        draw.text((50, PHOTO_H - 120), "  ·  ".join(meta_bits), font=f_meta, fill=(255, 235, 240))
    if plan.mood_id:
        draw.text((50, PHOTO_H - 70), plan.mood.name, font=f_meta, fill=(255, 235, 240))

    # --- Bloc QR code en bas ---------------------------------------------
    qr_img = qrcode.make(url, box_size=8, border=2).convert("RGB")
    qr_size = 340
    qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)

    footer_y = PHOTO_H + 40
    caption = "Scanne ce QR code pour découvrir l'invitation"
    caption_w = draw.textlength(caption, font=f_caption)
    draw.text(((W - caption_w) / 2, footer_y), caption, font=f_caption, fill=INK)

    qr_x = (W - qr_size) // 2
    qr_y = footer_y + 60
    draw.rounded_rectangle(
        [(qr_x - 24, qr_y - 24), (qr_x + qr_size + 24, qr_y + qr_size + 24)],
        radius=24, fill="white", outline=(230, 220, 224), width=2,
    )
    card.paste(qr_img, (qr_x, qr_y))

    small_y = qr_y + qr_size + 55
    short_url = url.replace("https://", "").replace("http://", "")
    if len(short_url) > 48:
        short_url = short_url[:47].rstrip() + "…"
    small_w = draw.textlength(short_url, font=f_small)
    draw.text(((W - small_w) / 2, small_y), short_url, font=f_small, fill=INK_SOFT)

    # Liseré de marque en tout bas.
    draw.rectangle([(0, H - 14), (W, H)], fill=ROSE)

    buffer = io.BytesIO()
    card.save(buffer, format="PNG")
    response = HttpResponse(buffer.getvalue(), content_type="image/png")
    response["Content-Disposition"] = f'attachment; filename="date-with-u-invitation-{invitation.token}.png"'
    return response


def _is_admin(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(_is_admin, login_url="accounts:login")
def admin_dashboard_view(request):
    """
    Tableau de bord admin AJAX — remplace l'usage quotidien du Django Admin
    par défaut (gardé en accès secours, déplacé via ADMIN_URL_PATH).
    """
    stats = {
        "total_users": User.objects.count(),
        "staff_users": User.objects.filter(is_staff=True).count(),
    }
    config = SiteConfiguration.load()
    return render(
        request,
        "core/admin_dashboard.html",
        {"stats": stats, "config": config, "admin_url_path": settings.ADMIN_URL_PATH},
    )


@login_required
def premium_view(request):
    """
    Page tarifs / upgrade Premium. Sans passerelle de paiement Mobile Money
    intégrée (MVola/Orange Money/Airtel Money — aucune n'expose d'API
    testable ici), la demande passe par une validation manuelle admin (voir
    apps.premium.models.Subscription) ; le formulaire précise clairement
    la marche à suivre en attendant une intégration automatisée.
    """
    from django.contrib import messages as dj_messages

    from apps.premium.models import PremiumPlan, Subscription

    plans = PremiumPlan.objects.filter(is_active=True)
    pending = Subscription.objects.filter(
        user=request.user, status=Subscription.STATUS_PENDING,
    ).select_related("plan").first()
    active = Subscription.objects.filter(
        user=request.user, status=Subscription.STATUS_ACTIVE,
    ).select_related("plan").order_by("-expires_at").first()

    if request.method == "POST" and not pending and not request.user.is_premium:
        plan_id = request.POST.get("plan_id")
        plan = plans.filter(pk=plan_id).first()
        if plan:
            Subscription.objects.create(
                user=request.user, plan=plan,
                payment_reference=request.POST.get("payment_reference", ""),
            )
            dj_messages.success(
                request,
                "Demande envoyée ! On valide généralement sous 24h après réception du paiement "
                "Mobile Money — tu seras notifié·e dès que ton compte Premium sera actif.",
            )
            return redirect("core:premium")

    return render(request, "core/premium.html", {
        "plans": plans, "pending": pending, "active": active,
    })


@login_required
def statistics_view(request):
    """
    Statistiques personnelles ("Ton année en rendez-vous") : nombre de
    rendez-vous créés, taux d'acceptation, ville/ambiance favorites,
    répartition par mois — données agrégées à la volée, pas de modèle dédié.
    """
    from collections import Counter
    import json

    from django.utils import timezone as dj_timezone

    from apps.invitations.models import Invitation
    from apps.planner.models import DatePlan

    plans = list(DatePlan.objects.filter(
        creator=request.user, status=DatePlan.STATUS_COMPLETED,
    ).select_related("city", "mood"))
    total = len(plans)
    invitations = Invitation.objects.filter(date_plan__creator=request.user)
    responded = invitations.exclude(status=Invitation.STATUS_PENDING).count()
    accepted = invitations.filter(status__in=[Invitation.STATUS_ACCEPTED, Invitation.STATUS_MAYBE]).count()
    acceptance_rate = round((accepted / responded) * 100) if responded else None

    city_counter = Counter(p.city.name for p in plans if p.city_id)
    mood_counter = Counter(p.mood.name for p in plans if p.mood_id)
    top_city = city_counter.most_common(1)[0][0] if city_counter else None
    top_mood = mood_counter.most_common(1)[0][0] if mood_counter else None

    today = dj_timezone.now().date()
    months_labels = []
    months_data = []
    for i in range(5, -1, -1):
        year, month = today.year, today.month - i
        while month <= 0:
            month += 12
            year -= 1
        months_labels.append(f"{month:02d}/{year}")
        months_data.append(sum(1 for p in plans if p.created_at.year == year and p.created_at.month == month))

    return render(request, "core/statistics.html", {
        "total": total,
        "acceptance_rate": acceptance_rate,
        "top_city": top_city,
        "top_mood": top_mood,
        "months_labels": json.dumps(months_labels),
        "months_data": json.dumps(months_data),
        "mood_labels": json.dumps(list(mood_counter.keys())),
        "mood_data": json.dumps(list(mood_counter.values())),
    })


def track_location_view(request, token):
    """Page publique (aucun compte requis) pour suivre la position en
    direct de quelqu'un qui a activé « Prévenir un proche »."""
    return render(request, "core/track_location.html", {"token": token})


@login_required
def date_ics_view(request, plan_id):
    """
    Export .ics d'un rendez-vous — « Ajouter à mon calendrier » (Google
    Calendar, Outlook, Apple Calendar comprennent tous ce format standard).
    Accessible au créateur et, si elle existe, à la personne invitée.
    """
    import datetime as dt

    from apps.planner.models import DatePlan

    plan = get_object_or_404(DatePlan, pk=plan_id)
    invitation = getattr(plan, "invitation", None)
    is_creator = plan.creator_id == request.user.id
    is_partner = invitation and invitation.partner_user_id == request.user.id
    if not (is_creator or is_partner):
        return HttpResponse("Accès non autorisé.", status=403)

    if not plan.date_value:
        return HttpResponse("Ce rendez-vous n'a pas encore de date fixée.", status=400)

    start_time = plan.time_value or dt.time(19, 0)
    start_dt = dt.datetime.combine(plan.date_value, start_time)
    end_dt = start_dt + dt.timedelta(hours=2)

    def fmt(d):
        return d.strftime("%Y%m%dT%H%M%S")

    summary = plan.place.name if plan.place_id else (plan.activity.name if plan.activity_id else "Rendez-vous Date With U")
    location = ""
    if plan.place_id:
        location = f"{plan.place.name}, {plan.place.address or ''}".strip(", ")
    elif plan.city_id:
        location = plan.city.name

    description = plan.personal_message or "Organisé avec Date With U."

    ics = "\r\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Date With U//FR",
        "BEGIN:VEVENT",
        f"UID:date-plan-{plan.id}@datewithu.mg",
        f"DTSTAMP:{fmt(timezone.now())}",
        f"DTSTART:{fmt(start_dt)}",
        f"DTEND:{fmt(end_dt)}",
        f"SUMMARY:{summary}",
        f"LOCATION:{location}",
        f"DESCRIPTION:{description}",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ])
    response = HttpResponse(ics, content_type="text/calendar")
    response["Content-Disposition"] = f'attachment; filename="rendez-vous-{plan.id}.ics"'
    return response


@login_required
def recommendations_api_view(request):
    """
    GET /recommandations/ (appelé en AJAX depuis le dashboard) — suggestions
    de lieux basées sur les ambiances/villes déjà choisies par l'utilisateur
    dans ses rendez-vous passés. Logique volontairement simple (pas de
    modèle ML) : compter les ambiances/villes les plus fréquentes, puis
    proposer les lieux les mieux notés qui correspondent, non déjà utilisés.
    """
    from collections import Counter

    from django.http import JsonResponse

    from apps.catalog.models import Place
    from apps.planner.models import DatePlan

    past_plans = DatePlan.objects.filter(
        creator=request.user, status=DatePlan.STATUS_COMPLETED,
    ).select_related("mood", "city")
    used_place_ids = set(past_plans.exclude(place__isnull=True).values_list("place_id", flat=True))

    mood_counter = Counter(p.mood_id for p in past_plans if p.mood_id)
    city_counter = Counter(p.city_id for p in past_plans if p.city_id)
    top_mood_id = mood_counter.most_common(1)[0][0] if mood_counter else None
    top_city_id = city_counter.most_common(1)[0][0] if city_counter else None

    qs = Place.objects.filter(is_active=True).exclude(id__in=used_place_ids)
    if top_city_id:
        qs = qs.filter(city_id=top_city_id)
    if top_mood_id:
        qs = qs.filter(activities__compatible_moods=top_mood_id)
    places = qs.select_related("city", "category").order_by("-rating").distinct()[:4]

    if not places:
        # Pas assez d'historique : on retombe sur les lieux les mieux notés,
        # tous critères confondus, plutôt que de ne rien montrer.
        places = Place.objects.filter(is_active=True).exclude(
            id__in=used_place_ids,
        ).order_by("-rating")[:4]

    data = [{
        "id": p.id,
        "name": p.name,
        "city": p.city.name if p.city_id else None,
        "category": p.category.name if p.category_id else None,
        "rating": float(p.rating),
        "main_image": p.main_image.url if p.main_image else None,
    } for p in places]
    return JsonResponse({"results": data})
