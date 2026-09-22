from rest_framework import permissions


class IsStaffUser(permissions.BasePermission):
    """Autorise uniquement les membres du staff (is_staff=True) — section
    « Dashboard admin » : toutes les vues de modération/statistiques
    passent par cette permission plutôt que par le Django Admin brut."""

    message = "Réservé aux administrateurs."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
