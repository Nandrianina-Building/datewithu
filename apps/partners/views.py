from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.catalog.models import Place
from apps.reviews.models import Review

from .forms import PlaceClaimForm, PlaceEditForm
from .models import PlaceClaim


@login_required
def claim_place_view(request, place_id):
    """Formulaire pour revendiquer la gestion d'un lieu (« Ce lieu est le
    vôtre ? » — feature B2B classique)."""
    place = get_object_or_404(Place, pk=place_id)
    existing = PlaceClaim.objects.filter(place=place, user=request.user).first()

    if existing:
        messages.info(request, "Tu as déjà une demande pour ce lieu.")
        return redirect("partners:dashboard")

    if request.method == "POST":
        form = PlaceClaimForm(request.POST)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.place = place
            claim.user = request.user
            claim.save()
            messages.success(
                request,
                "Demande envoyée ! On vérifie ton lien avec l'établissement et "
                "on te donne accès à l'édition de la fiche sous peu.",
            )
            return redirect("partners:dashboard")
    else:
        form = PlaceClaimForm()

    return render(request, "partners/claim_place.html", {"place": place, "form": form})


@login_required
def partner_dashboard_view(request):
    """Vue d'ensemble des lieux gérés (revendications approuvées), avec
    quelques statistiques simples (vues, nombre d'avis, note moyenne)."""
    claims = PlaceClaim.objects.filter(user=request.user).select_related("place")
    approved_places = [c.place for c in claims if c.status == PlaceClaim.STATUS_APPROVED]

    stats = []
    for place in approved_places:
        reviews = Review.objects.filter(place=place)
        stats.append({
            "place": place,
            "view_count": place.view_count,
            "review_count": reviews.count(),
            "rating": place.rating,
            "pending_replies": reviews.filter(owner_reply="").count(),
        })

    return render(request, "partners/dashboard.html", {"claims": claims, "stats": stats})


@login_required
def edit_claimed_place_view(request, place_id):
    place = get_object_or_404(Place, pk=place_id)
    claim = PlaceClaim.objects.filter(
        place=place, user=request.user, status=PlaceClaim.STATUS_APPROVED,
    ).first()
    if not claim:
        messages.error(request, "Tu n'as pas (ou plus) les droits d'édition sur ce lieu.")
        return redirect("partners:dashboard")

    if request.method == "POST":
        form = PlaceEditForm(request.POST, instance=place)
        if form.is_valid():
            form.save()
            messages.success(request, "Fiche mise à jour.")
            return redirect("partners:dashboard")
    else:
        form = PlaceEditForm(instance=place)

    reviews = Review.objects.filter(place=place).order_by("-created_at")[:20]
    return render(request, "partners/edit_place.html", {"place": place, "form": form, "reviews": reviews})


@login_required
def reply_to_review_view(request, review_id):
    """POST uniquement : répondre publiquement à un avis, réservé au
    partenaire ayant une revendication approuvée sur ce lieu."""
    review = get_object_or_404(Review, pk=review_id)
    has_rights = PlaceClaim.objects.filter(
        place=review.place, user=request.user, status=PlaceClaim.STATUS_APPROVED,
    ).exists()
    if not has_rights or request.method != "POST":
        messages.error(request, "Action non autorisée.")
        return redirect("partners:dashboard")

    review.owner_reply = request.POST.get("owner_reply", "").strip()
    review.owner_reply_at = timezone.now() if review.owner_reply else None
    review.save(update_fields=["owner_reply", "owner_reply_at"])
    messages.success(request, "Réponse publiée.")
    return redirect("partners:edit_place", place_id=review.place_id)
